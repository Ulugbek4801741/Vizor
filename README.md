# VIZOR

VIZOR is a standalone learning platform for students, teachers, parents, and administrators.

## Initial deployment

This repository is being prepared for deployment on Render. The first release provides a FastAPI backend, health checks, API documentation, and PostgreSQL-backed data models. The web interface and learning modules will be added in staged releases.



## Guest access

Registration is optional. The web page opens in guest mode by default and stores a random guest session ID in the browser.

- `GET /` — VIZOR web entry page with guest mode and optional account login/registration.
- `GET /api/courses` — list published courses without an account.
- `GET /api/courses/{course_id}/lessons` — read lessons in a published course without an account.
- `GET /api/courses/{course_id}/quizzes` — read quizzes for a published course.
- `POST /api/lessons/{lesson_id}/complete` — save lesson completion. Guests send their browser session in the `X-Guest-ID` header; signed-in students use their Bearer token.
- `GET /api/guest/progress` — retrieve guest progress using the same `X-Guest-ID` header.

Guest access covers public learning content and guest progress. Creating/publishing courses, editing teaching content, and administration remain protected by account roles. Guest progress is tied to the browser's local guest ID; clearing browser storage or switching devices starts a separate guest history.


## Android ilova

Android WebView ilovasi `android/` papkasida. Ilova birinchi ishga tushganda VIZOR Render serverining HTTPS manzilini so‘raydi va saqlaydi. Shu sababli server URL tayyor bo‘lgach uni ilovaga kiritish kerak.

- Android Studio: `android/` papkasini oching va Debug APK yarating.
- GitHub Actions: Android fayllari o‘zgarganda `vizor-android-debug` APK artefaktini yaratishga mo‘ljallangan workflow mavjud.
- Hozircha bu imzolangan Play Store relizi emas; release signing key alohida sozlanadi.
