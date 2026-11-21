"""VIZOR education marketplace API.

Paid-course requests are recorded as pending until an administrator verifies
payment and approves access. No payment provider is implied by this module.
"""
from datetime import datetime
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, Session

from app.main import Base, Course, Lesson, User, get_db, current_user, optional_user, require_roles

router = APIRouter(prefix="/api/education", tags=["education"])


class CourseOffer(Base):
    __tablename__ = "course_offers"
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True)
    is_free: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    price_minor: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="UZS", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CourseAccessRequest(Base):
    __tablename__ = "course_access_requests"
    __table_args__ = (UniqueConstraint("course_id", "student_id", name="uq_course_access_student"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    reviewer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class LessonAsset(Base):
    __tablename__ = "lesson_assets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200))
    url: Mapped[Optional[str]] = mapped_column(String(1200), nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=1)


class PracticalTask(Base):
    __tablename__ = "practical_tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    instructions: Mapped[str] = mapped_column(Text)
    submission_type: Mapped[str] = mapped_column(String(20), default="text")
    position: Mapped[int] = mapped_column(Integer, default=1)


class PracticalSubmission(Base):
    __tablename__ = "practical_submissions"
    __table_args__ = (UniqueConstraint("task_id", "student_id", name="uq_practical_submission_student"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("practical_tasks.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    answer: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="submitted")
    teacher_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OfferIn(BaseModel):
    is_free: bool
    price_minor: int = Field(default=0, ge=0, le=100000000000)
    currency: str = Field(default="UZS", min_length=3, max_length=3)


class AssetIn(BaseModel):
    kind: Literal["video", "pdf", "text", "link"]
    title: str = Field(min_length=2, max_length=200)
    url: Optional[str] = Field(default=None, max_length=1200)
    body: Optional[str] = None
    position: int = Field(default=1, ge=1, le=10000)


class PracticalIn(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    instructions: str = Field(min_length=5)
    submission_type: Literal["text", "file_link"] = "text"
    position: int = Field(default=1, ge=1, le=10000)


class SubmissionIn(BaseModel):
    answer: str = Field(min_length=1, max_length=20000)


def _course_or_404(db: Session, course_id: int):
    course = db.get(Course, course_id)
    if not course or not course.published:
        raise HTTPException(404, "Kurs topilmadi")
    return course


def _owns_course(course: Course, user: User):
    if user.role != "admin" and course.teacher_id != user.id:
        raise HTTPException(403, "Bu kursni boshqarish huquqi yo‘q")


def _has_access(db: Session, course_id: int, user: Optional[User], offer: Optional[CourseOffer]):
    if offer is None or offer.is_free:
        return True
    if user is None:
        return False
    course = db.get(Course, course_id)
    if user.role == "admin" or (course and course.teacher_id == user.id):
        return True
    request = db.query(CourseAccessRequest).filter_by(
        course_id=course_id, student_id=user.id, status="approved"
    ).first()
    return request is not None


@router.get("/catalog")
def education_catalog(db: Session = Depends(get_db)):
    courses = db.query(Course).filter(Course.published.is_(True)).order_by(Course.id.desc()).all()
    result = []
    for course in courses:
        offer = db.get(CourseOffer, course.id)
        lessons_count = db.query(Lesson).filter_by(course_id=course.id).count()
        result.append({
            "id": course.id, "title": course.title, "description": course.description,
            "category": course.category, "teacher_id": course.teacher_id,
            "is_free": True if offer is None else offer.is_free,
            "price_minor": 0 if offer is None else offer.price_minor,
            "currency": "UZS" if offer is None else offer.currency,
            "lessons_count": lessons_count
        })
    return result


@router.get("/courses/{course_id}/materials")
def course_materials(course_id: int, db: Session = Depends(get_db), user: Optional[User] = Depends(optional_user)):
    course = _course_or_404(db, course_id)
    offer = db.get(CourseOffer, course_id)
    if not _has_access(db, course_id, user, offer):
        raise HTTPException(402, "Bu pullik kurs. Darslarni ochish uchun kursga ruxsat oling.")
    lessons = db.query(Lesson).filter_by(course_id=course_id).order_by(Lesson.position).all()
    lesson_data = []
    for lesson in lessons:
        assets = db.query(LessonAsset).filter_by(lesson_id=lesson.id).order_by(LessonAsset.position).all()
        lesson_data.append({
            "id": lesson.id, "title": lesson.title, "content": lesson.content,
            "video_url": lesson.video_url, "position": lesson.position,
            "assets": [{"id": a.id, "kind": a.kind, "title": a.title, "url": a.url, "body": a.body} for a in assets]
        })
    tasks = db.query(PracticalTask).filter_by(course_id=course_id).order_by(PracticalTask.position).all()
    return {
        "course": {"id": course.id, "title": course.title, "category": course.category},
        "lessons": lesson_data,
        "practicals": [{"id": t.id, "title": t.title, "instructions": t.instructions, "submission_type": t.submission_type} for t in tasks]
    }


@router.put("/courses/{course_id}/offer")
def set_course_offer(course_id: int, data: OfferIn, db: Session = Depends(get_db), user: User = Depends(require_roles("teacher", "admin"))):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(404, "Kurs topilmadi")
    _owns_course(course, user)
    offer = db.get(CourseOffer, course_id)
    if offer is None:
        offer = CourseOffer(course_id=course_id, is_free=data.is_free, price_minor=0 if data.is_free else data.price_minor, currency=data.currency.upper())
        db.add(offer)
    else:
        offer.is_free = data.is_free
        offer.price_minor = 0 if data.is_free else data.price_minor
        offer.currency = data.currency.upper()
    db.commit()
    return {"course_id": course_id, "is_free": offer.is_free, "price_minor": offer.price_minor, "currency": offer.currency}


@router.post("/courses/{course_id}/access-request", status_code=201)
def request_course_access(course_id: int, payment_reference: Optional[str] = None, db: Session = Depends(get_db), user: User = Depends(current_user)):
    course = _course_or_404(db, course_id)
    offer = db.get(CourseOffer, course_id)
    if offer is None or offer.is_free:
        raise HTTPException(409, "Bu kurs bepul. Darslarni darhol ochishingiz mumkin.")
    if user.role not in ("student", "parent"):
        raise HTTPException(403, "Faqat o‘quvchi yoki ota-ona kursga ruxsat so‘rashi mumkin")
    existing = db.query(CourseAccessRequest).filter_by(course_id=course_id, student_id=user.id).first()
    if existing:
        if existing.status == "approved":
            return {"id": existing.id, "status": "approved"}
        if existing.status == "pending":
            return {"id": existing.id, "status": "pending", "message": "So‘rovingiz tekshirilmoqda"}
        existing.status = "pending"
        existing.payment_reference = payment_reference
        existing.created_at = datetime.utcnow()
        db.commit()
        return {"id": existing.id, "status": "pending"}
    request = CourseAccessRequest(course_id=course.id, student_id=user.id, payment_reference=payment_reference)
    db.add(request)
    db.commit()
    db.refresh(request)
    return {"id": request.id, "status": request.status, "message": "To‘lov tasdiqlangach administrator kursni ochadi"}


@router.post("/lessons/{lesson_id}/assets", status_code=201)
def add_lesson_asset(lesson_id: int, data: AssetIn, db: Session = Depends(get_db), user: User = Depends(require_roles("teacher", "admin"))):
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Dars topilmadi")
    course = db.get(Course, lesson.course_id)
    _owns_course(course, user)
    if data.kind in ("video", "pdf", "link") and not data.url:
        raise HTTPException(400, "Bu material turi uchun URL kerak")
    if data.kind == "text" and not (data.body or "").strip():
        raise HTTPException(400, "Matnli dars bo‘sh bo‘lmasligi kerak")
    asset = LessonAsset(lesson_id=lesson_id, kind=data.kind, title=data.title, url=data.url, body=data.body, position=data.position)
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return {"id": asset.id, "lesson_id": lesson_id, "kind": asset.kind, "title": asset.title}


@router.post("/courses/{course_id}/practicals", status_code=201)
def create_practical(course_id: int, data: PracticalIn, db: Session = Depends(get_db), user: User = Depends(require_roles("teacher", "admin"))):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(404, "Kurs topilmadi")
    _owns_course(course, user)
    task = PracticalTask(course_id=course_id, title=data.title, instructions=data.instructions, submission_type=data.submission_type, position=data.position)
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"id": task.id, "course_id": course_id, "title": task.title}


@router.post("/practicals/{task_id}/submit", status_code=201)
def submit_practical(task_id: int, data: SubmissionIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.role != "student":
        raise HTTPException(403, "Topshiriqni faqat o‘quvchi yuborishi mumkin")
    task = db.get(PracticalTask, task_id)
    if not task:
        raise HTTPException(404, "Amaliy topshiriq topilmadi")
    offer = db.get(CourseOffer, task.course_id)
    if not _has_access(db, task.course_id, user, offer):
        raise HTTPException(402, "Bu pullik kurs uchun ruxsat kerak")
    submission = db.query(PracticalSubmission).filter_by(task_id=task_id, student_id=user.id).first()
    if submission is None:
        submission = PracticalSubmission(task_id=task_id, student_id=user.id, answer=data.answer)
        db.add(submission)
    else:
        submission.answer = data.answer
        submission.status = "resubmitted"
    db.commit()
    db.refresh(submission)
    return {"id": submission.id, "task_id": task_id, "status": submission.status}


@router.get("/access-requests")
def list_access_requests(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    rows = db.query(CourseAccessRequest).order_by(CourseAccessRequest.created_at.desc()).limit(200).all()
    return [{"id": r.id, "course_id": r.course_id, "student_id": r.student_id, "status": r.status, "payment_reference": r.payment_reference, "created_at": r.created_at} for r in rows]


@router.post("/access-requests/{request_id}/approve")
def approve_access_request(request_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    request = db.get(CourseAccessRequest, request_id)
    if not request:
        raise HTTPException(404, "So‘rov topilmadi")
    request.status = "approved"
    request.reviewer_id = user.id
    request.reviewed_at = datetime.utcnow()
    db.commit()
    return {"id": request.id, "status": request.status, "course_id": request.course_id, "student_id": request.student_id}
