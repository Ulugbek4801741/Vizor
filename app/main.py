import os
import json
import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.responses import HTMLResponse, Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import create_engine, String, Text, Integer, Boolean, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session, relationship

APP_VERSION = "0.3.0"
DATABASE_URL = os.getenv("DATABASE_URL", "")
JWT_SECRET = os.getenv("JWT_SECRET", "development-only-change-me")
JWT_ALGORITHM = "HS256"

engine = None
SessionLocal = None
if DATABASE_URL:
    db_url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(db_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(20), default="student")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(80), default="general")
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Lesson(Base):
    __tablename__ = "lessons"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text, default="")
    video_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=1)

class Enrollment(Base):
    __tablename__ = "enrollments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Quiz(Base):
    __tablename__ = "quizzes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    questions_json: Mapped[str] = mapped_column(Text, default="[]")

class GuestProgress(Base):
    __tablename__ = "guest_lesson_progress"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    guest_key: Mapped[str] = mapped_column(String(80), index=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Progress(Base):
    __tablename__ = "lesson_progress"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

def get_db():
    if SessionLocal is None:
        raise HTTPException(503, "Database is not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310000)
    return salt.hex() + "$" + digest.hex()

def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 310000)
        return hmac.compare_digest(actual.hex(), digest_hex)
    except Exception:
        return False

def issue_token(user: User) -> str:
    return jwt.encode({"sub": str(user.id), "role": user.role, "exp": datetime.now(timezone.utc) + timedelta(hours=24)}, JWT_SECRET, algorithm=JWT_ALGORITHM)

bearer = HTTPBearer(auto_error=False)
def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
    if not credentials:
        raise HTTPException(401, "Authentication required")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = db.get(User, int(payload["sub"]))
    except Exception:
        user = None
    if not user or not user.active:
        raise HTTPException(401, "Invalid or expired token")
    return user

def optional_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = db.get(User, int(payload["sub"]))
        return user if user and user.active else None
    except Exception:
        return None

def optional_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("role") == "guest":
            return None
        user = db.get(User, int(payload["sub"]))
    except Exception:
        raise HTTPException(401, "Invalid or expired token")
    if not user or not user.active:
        raise HTTPException(401, "Invalid or expired token")
    return user

def require_roles(*roles):
    def check(user: User = Depends(current_user)):
        if user.role not in roles:
            raise HTTPException(403, "Permission denied")
        return user
    return check

app = FastAPI(title="VIZOR Learning Platform API", version=APP_VERSION, description="Standalone VIZOR education platform API")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "*").split(","), allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
def startup():
    if engine is not None:
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            if db.query(Course).count() == 0:
                demo_teacher = User(full_name="VIZOR ta’lim jamoasi", email="platform@vizor.local", password_hash=hash_password(uuid.uuid4().hex), role="teacher")
                db.add(demo_teacher)
                db.flush()
                demo_course = Course(title="Raqamli savodxonlik — boshlang‘ich", description="Internetdan xavfsiz foydalanish, kuchli parol va foydali raqamli odatlar.", category="Raqamli savodxonlik", published=True, teacher_id=demo_teacher.id)
                db.add(demo_course)
                db.flush()
                demo_lessons = [
                    Lesson(course_id=demo_course.id, title="Internet xavfsizligi", content="Shaxsiy ma’lumotlaringizni himoya qiling. Parollarni boshqa odamlarga bermang, noma’lum havolalarni ochmang va har bir xizmat uchun alohida parol ishlating.", position=1),
                    Lesson(course_id=demo_course.id, title="Kuchli parol yaratish", content="Kuchli parol uzun bo‘ladi, katta-kichik harflar, raqamlar va belgilarni aralashtiradi. Imkon bo‘lsa, ikki bosqichli tasdiqlashni yoqing.", position=2),
                    Lesson(course_id=demo_course.id, title="Onlayn ma’lumotni tekshirish", content="Xabar manbasini tekshiring, sanasiga qarang va muhim ma’lumotni kamida ikki ishonchli manba bilan solishtiring.", position=3)
                ]
                db.add_all(demo_lessons)
                db.flush()
                db.add(Quiz(course_id=demo_course.id, title="Raqamli savodxonlik testi", questions_json=json.dumps([
                    {"question":"Noma’lum havola kelsa nima qilish kerak?","options":["Darhol ochish","Manbasini tekshirish va shubhali bo‘lsa ochmaslik","Hammaga yuborish"],"answer_index":1},
                    {"question":"Kuchli parol qanday bo‘ladi?","options":["123456","Ism va tug‘ilgan yil","Uzun va murakkab, har xizmat uchun alohida"],"answer_index":2},
                    {"question":"Muhim xabarni qanday tekshirish kerak?","options":["Faqat sarlavhaga ishonish","Bir nechta ishonchli manba bilan solishtirish","Darhol ulashish"],"answer_index":1}
                ], ensure_ascii=False)))
                db.commit()

class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = "student"

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class CourseIn(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str = ""
    category: str = "general"

class LessonIn(BaseModel):
    title: str
    content: str = ""
    video_url: Optional[str] = None
    position: int = 1

class QuizIn(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    questions: list[dict] = Field(min_length=1, max_length=100)

@app.get("/")
def root():
    return FileResponse("app/static/index.html")

@app.get("/api/public/courses")
def public_courses(db: Session = Depends(get_db)):
    rows = db.query(Course).filter(Course.published.is_(True)).order_by(Course.id.desc()).all()
    return [{"id": c.id, "title": c.title, "description": c.description, "category": c.category, "teacher_id": c.teacher_id} for c in rows]

@app.get("/health")
def health():
    return {"status": "ok", "service": "vizor-api", "version": APP_VERSION, "database_configured": SessionLocal is not None}

@app.get("/manifest.webmanifest")
def manifest():
    return {"name": "VIZOR — Ochiq ta’lim platformasi", "short_name": "VIZOR", "lang": "uz", "start_url": "/", "scope": "/", "display": "standalone", "background_color": "#eaf5ff", "theme_color": "#0878ed", "description": "Ochiq kurslar, darslar va bilim sinovlari"}

@app.get("/sw.js")
def service_worker():
    return Response("""const CACHE='vizor-shell-v5'; self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(['/'])))); self.addEventListener('activate',e=>e.waitUntil(self.clients.claim())); self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return; const u=new URL(e.request.url); if(u.origin!==location.origin)return; if(u.pathname.startsWith('/api/'))return; e.respondWith(fetch(e.request).then(r=>{if(r.ok){const copy=r.clone();caches.open(CACHE).then(c=>c.put(e.request,copy));}return r;}).catch(()=>caches.match(e.request).then(r=>r||caches.match('/'))));});""", media_type="application/javascript")

@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    db.execute(func.now().select())
    return {"ready": True, "database": "connected"}

@app.post("/api/auth/register", status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if data.role not in ("student", "teacher", "parent"):
        raise HTTPException(400, "Allowed roles: student, teacher, parent")
    email = data.email.lower()
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(409, "Email already registered")
    user = User(full_name=data.full_name, email=email, password_hash=hash_password(data.password), role=data.role)
    db.add(user); db.commit(); db.refresh(user)
    return {"access_token": issue_token(user), "token_type": "bearer", "user": {"id": user.id, "full_name": user.full_name, "email": user.email, "role": user.role}}

@app.post("/api/auth/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Email or password is incorrect")
    return {"access_token": issue_token(user), "token_type": "bearer", "user": {"id": user.id, "full_name": user.full_name, "email": user.email, "role": user.role}}

@app.get("/api/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "full_name": user.full_name, "email": user.email, "role": user.role}

@app.get("/api/courses")
def courses(db: Session = Depends(get_db), user: Optional[User] = Depends(optional_user)):
    rows = db.query(Course).filter(Course.published.is_(True)).order_by(Course.id.desc()).all()
    return [{"id": c.id, "title": c.title, "description": c.description, "category": c.category, "teacher_id": c.teacher_id} for c in rows]

@app.post("/api/courses", status_code=201)
def create_course(data: CourseIn, db: Session = Depends(get_db), user: User = Depends(require_roles("teacher", "admin"))):
    course = Course(title=data.title, description=data.description, category=data.category, teacher_id=user.id)
    db.add(course); db.commit(); db.refresh(course)
    return {"id": course.id, "title": course.title, "published": course.published}

@app.post("/api/courses/{course_id}/publish")
def publish_course(course_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("teacher", "admin"))):
    course = db.get(Course, course_id)
    if not course or (user.role != "admin" and course.teacher_id != user.id):
        raise HTTPException(404, "Course not found")
    course.published = True; db.commit()
    return {"id": course.id, "published": True}

@app.post("/api/courses/{course_id}/lessons", status_code=201)
def add_lesson(course_id: int, data: LessonIn, db: Session = Depends(get_db), user: User = Depends(require_roles("teacher", "admin"))):
    course = db.get(Course, course_id)
    if not course or (user.role != "admin" and course.teacher_id != user.id):
        raise HTTPException(404, "Course not found")
    lesson = Lesson(course_id=course_id, title=data.title, content=data.content, video_url=data.video_url, position=data.position)
    db.add(lesson); db.commit(); db.refresh(lesson)
    return {"id": lesson.id, "course_id": course_id, "title": lesson.title}

@app.get("/api/courses/{course_id}/lessons")
def list_lessons(course_id: int, db: Session = Depends(get_db), user: Optional[User] = Depends(optional_user)):
    course = db.get(Course, course_id)
    if not course or (not course.published and (user is None or (course.teacher_id != user.id and user.role != "admin"))):
        raise HTTPException(404, "Course not found")
    rows = db.query(Lesson).filter_by(course_id=course_id).order_by(Lesson.position).all()
    return [{"id": l.id, "title": l.title, "content": l.content, "video_url": l.video_url, "position": l.position} for l in rows]

@app.post("/api/lessons/{lesson_id}/complete")
def complete_lesson(lesson_id: int, guest_key: Optional[str] = Header(default=None, alias="X-Guest-ID"), db: Session = Depends(get_db), user: Optional[User] = Depends(optional_user)):
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    if user is not None and user.role == "student":
        row = db.query(Progress).filter_by(student_id=user.id, lesson_id=lesson_id).first()
        if row is None:
            db.add(Progress(student_id=user.id, lesson_id=lesson_id, completed=True))
        else:
            row.completed = True
        db.commit()
        return {"lesson_id": lesson_id, "completed": True, "saved": "account"}
    if not guest_key or len(guest_key) < 16 or len(guest_key) > 80:
        raise HTTPException(400, "Guest session ID required")
    course = db.get(Course, lesson.course_id)
    if not course or not course.published:
        raise HTTPException(404, "Lesson not found")
    row = db.query(GuestProgress).filter_by(guest_key=guest_key, lesson_id=lesson_id).first()
    if row is None:
        db.add(GuestProgress(guest_key=guest_key, lesson_id=lesson_id, completed=True))
    else:
        row.completed = True
    db.commit()
    return {"lesson_id": lesson_id, "completed": True, "saved": "guest-session", "saved_on_server": True}

@app.get("/api/guest/progress")
def guest_progress(guest_key: Optional[str] = Header(default=None, alias="X-Guest-ID"), db: Session = Depends(get_db)):
    if not guest_key or len(guest_key) < 16 or len(guest_key) > 80:
        raise HTTPException(400, "Guest session ID required")
    rows = db.query(GuestProgress).filter_by(guest_key=guest_key, completed=True).all()
    return {"mode": "guest", "completed_lesson_ids": [row.lesson_id for row in rows], "count": len(rows)}

@app.get("/api/courses/{course_id}/quizzes")
def list_quizzes(course_id: int, db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course or not course.published:
        raise HTTPException(404, "Course not found")
    rows = db.query(Quiz).filter_by(course_id=course_id).all()
    safe = []
    for quiz in rows:
        questions = json.loads(quiz.questions_json or "[]")
        safe_questions = []
        for index, question in enumerate(questions):
            safe_questions.append({
                "id": index,
                "question": str(question.get("question", "")),
                "options": question.get("options", [])
            })
        safe.append({"id": quiz.id, "title": quiz.title, "questions": safe_questions})
    return safe

class QuizSubmitIn(BaseModel):
    answers: dict[str, int] = Field(default_factory=dict)

@app.post("/api/quizzes/{quiz_id}/submit")
def submit_quiz(
    quiz_id: int,
    data: QuizSubmitIn,
    guest_key: Optional[str] = Header(default=None, alias="X-Guest-ID"),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(optional_current_user)
):
    quiz = db.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    course = db.get(Course, quiz.course_id)
    if not course or not course.published:
        raise HTTPException(404, "Quiz not found")
    questions = json.loads(quiz.questions_json or "[]")
    if not questions:
        raise HTTPException(400, "Quiz has no questions")
    correct = 0
    details = []
    for index, question in enumerate(questions):
        options = question.get("options", [])
        answer = data.answers.get(str(index))
        valid = isinstance(answer, int) and 0 <= answer < len(options)
        is_correct = valid and answer == question.get("answer_index")
        correct += int(is_correct)
        details.append({"question_id": index, "correct": bool(is_correct)})
    if user is None and (not guest_key or len(guest_key) < 16 or len(guest_key) > 80):
        raise HTTPException(400, "Guest session ID required")
    return {
        "quiz_id": quiz.id,
        "score": correct,
        "total": len(questions),
        "percentage": round(correct * 100 / len(questions)),
        "passed": correct * 100 >= len(questions) * 60,
        "details": details
    }

@app.post("/api/courses/{course_id}/quizzes", status_code=201)
def create_quiz(course_id: int, data: QuizIn, db: Session = Depends(get_db), user: User = Depends(require_roles("teacher", "admin"))):
    course = db.get(Course, course_id)
    if not course or (user.role != "admin" and course.teacher_id != user.id):
        raise HTTPException(404, "Course not found")
    quiz = Quiz(course_id=course_id, title=data.title, questions_json=json.dumps(data.questions, ensure_ascii=False))
    db.add(quiz); db.commit(); db.refresh(quiz)
    return {"id": quiz.id, "title": quiz.title, "question_count": len(data.questions)}

@app.get("/api/admin/overview")
def admin_overview(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    return {"users": db.query(User).count(), "courses": db.query(Course).count(), "lessons": db.query(Lesson).count(), "enrollments": db.query(Enrollment).count()}

@app.get("/api/system/status")
def system_status(db: Session = Depends(get_db)):
    return {"api": "online", "database": "connected", "version": APP_VERSION}
