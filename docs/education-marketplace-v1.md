# VIZOR Education Marketplace — v1 foundation

This branch adds an additive education API layer to the existing VIZOR app. It keeps the current guest-access, authentication, lessons, quizzes, and course endpoints intact.

## Course model

- Free courses: catalog metadata and lesson materials are available without an account.
- Paid courses: catalog metadata remains public; lesson materials require an approved access request.
- Teachers/admins can set a course offer as free or paid.
- Paid-course access requests are stored as `pending`; an administrator approves them only after verifying payment through the payment channel used by the platform.

**Important:** this foundation does not claim to charge cards or process online payments. A payment provider and verified webhook must be selected and configured before automatic payment confirmation is enabled.

## Learning materials

A lesson can keep its existing text and video URL. Additional lesson assets support:
- `video`: URL to a hosted video
- `pdf`: URL to a PDF document
- `text`: additional text content stored in the database
- `link`: external learning resource

Practical tasks support text or file-link submissions. Existing quizzes and exam scoring APIs remain available.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/education/catalog` | Published courses with free/paid price metadata |
| GET | `/api/education/courses/{id}/materials` | Lessons, PDF/video/text assets and practical tasks (access controlled) |
| PUT | `/api/education/courses/{id}/offer` | Teacher/admin sets free or paid offer |
| POST | `/api/education/courses/{id}/access-request` | Signed-in learner requests paid-course access |
| POST | `/api/education/lessons/{id}/assets` | Teacher/admin adds a PDF, video, text or external link |
| POST | `/api/education/courses/{id}/practicals` | Teacher/admin creates a practical task |
| POST | `/api/education/practicals/{id}/submit` | Student submits a practical answer |
| GET | `/api/education/access-requests` | Admin lists access requests |
| POST | `/api/education/access-requests/{id}/approve` | Admin approves verified payment/access |

## Price format

`price_minor` is stored as an integer in the smallest currency unit. For UZS, send the whole so'm amount (e.g. `150000`) and use `currency: "UZS"`.

## Deployment

The Render service currently tracks `feature/guest-access`. This implementation is isolated on `feature/education-marketplace-v1` and should be merged into the tracked branch only after review and a successful build/test run.
