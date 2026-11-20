# VIZOR

VIZOR is a standalone learning platform for students, teachers, parents, and administrators.

## Initial deployment

This repository is being prepared for deployment on Render. The first release provides a FastAPI backend, health checks, API documentation, and PostgreSQL-backed data models. The web interface and learning modules will be added in staged releases.


## Guest access

Registration is optional for public learning content. The API creates a temporary guest session and stores guest lesson progress in PostgreSQL.

- `POST /api/guest/session` — create a 30-day guest token.
- `GET /api/courses` — list published courses without an account.
- `GET /api/courses/{course_id}/lessons` — read lessons in a published course without an account.
- `POST /api/guest/lessons/{lesson_id}/complete` — save a guest's lesson completion on the server. Send the guest token as a Bearer token.
- `GET /api/guest/progress` — retrieve progress for that guest token.

Example:

```bash
TOKEN=$(curl -s -X POST https://YOUR-VIZOR-HOST/api/guest/session | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -H "Authorization: Bearer $TOKEN" https://YOUR-VIZOR-HOST/api/courses
```

Guest access is intentionally limited to public learning features. Creating courses, publishing lessons, teacher-only content, and administration still require an authenticated account with the appropriate role. Guest progress is associated with the browser's stored guest token; clearing that token loses the ability to retrieve that guest history.
