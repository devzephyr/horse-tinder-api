# Horse Tinder API

A horse matchmaking REST API built to demonstrate secure API development following the **OWASP API Security Top 10 (2023)**.

Every design decision in this project maps to a specific OWASP item. This is a working, tested API with dedicated security tests for each vulnerability category.

## Inspiration

This project was inspired by the [OWASP Toronto](https://owasp.org/www-chapter-toronto/) meetup on April 15, 2026, featuring a talk by **Dan Barahona** (co-founder of [APIsec](https://www.apisec.ai/) and [APIsec University](https://www.apisec.ai/university)) titled **"Why APIs Are Every Attacker's Favorite Target."**

Key takeaways from the talk that shaped this project:

- **APIs now carry 83% of internet traffic**, making them the primary attack surface for modern applications.
- The **OWASP API Security Top 10 (2023)** provides a concrete framework for understanding and mitigating the most critical API vulnerabilities.
- The **"big three"** -- Broken Object Level Authorization (API1), Broken Authentication (API2), and Broken Object Property Level Authorization (API3) -- account for roughly **90% of real-world API breaches**.
- Dan walked through real breach case studies mapped to specific OWASP items: McDonald's (BOLA/API1), Duolingo (broken auth/API2), Venmo (excessive data exposure/API3), a Formula 1 app (mass assignment/API3), Trello (brute force/API2), Bumble (broken function-level auth/API5), Instagram (business flow abuse/API6), and Coinbase (missing server-side validation).

The talk reinforced that API security is not an afterthought -- it needs to be baked into every layer of the application. This project puts that principle into practice by implementing mitigations for all 10 OWASP API Security items with corresponding security tests that verify each one.

## Tech Stack

- **Runtime:** Python 3.12+ / FastAPI (async)
- **Database:** PostgreSQL / SQLAlchemy 2.0 (async) / Alembic
- **Auth:** PyJWT / bcrypt / OAuth2 Bearer
- **Rate Limiting:** slowapi
- **Testing:** pytest / httpx / aiosqlite (test DB)

## Quick Start

```bash
# 1. Clone and install
git clone <repo-url> && cd api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 2. Start PostgreSQL
docker compose up -d

# 3. Configure environment
cp .env.example .env
# Edit .env with real secrets (generate with: python -c "import secrets; print(secrets.token_hex(32))")

# 4. Run migrations
alembic upgrade head

# 5. Seed with famous horses (optional)
python -m app.db.seed

# 6. Start the server
uvicorn app.main:app --reload

# 7. Open docs
open http://localhost:8000/docs
```

## OWASP API Security Top 10 (2023) -- Implementation Map

| # | Vulnerability | How This API Addresses It | Key Files |
|---|---|---|---|
| API1 | Broken Object Level Authorization | UUID primary keys. Service-layer ownership checks in WHERE clauses. Returns 404 (not 403) on unauthorized access to prevent existence confirmation. | `app/services/*.py`, `tests/security/test_bola.py` |
| API2 | Broken Authentication | JWT access tokens (15min) + refresh tokens (7d) with rotation. bcrypt hashing (12 rounds). Account lockout after 5 failed attempts for 30 minutes. | `app/core/security.py`, `app/services/auth_service.py`, `tests/security/test_auth_security.py` |
| API3 | Broken Object Property Level Authorization | Separate Create/Update/Read Pydantic schemas. `role` never accepted from client input. `hashed_password` never included in API responses. Explicit allowlists for writable fields. | `app/schemas/*.py`, `tests/security/test_property_auth.py` |
| API4 | Unrestricted Resource Consumption | slowapi rate limiting (per-user and per-IP). Enforced max `page_size=50`. 1MB request body limit. Max 5 horses per user, 10 photos per horse. | `app/core/rate_limiter.py`, `app/schemas/pagination.py`, `tests/security/test_resource_limits.py` |
| API5 | Broken Function Level Authorization | `get_current_admin` dependency applied at router level to all `/admin/*` routes. Role-based access control (user/admin). Returns 403 for unauthorized function access. | `app/core/dependencies.py`, `app/api/v1/admin.py`, `tests/security/test_function_auth.py` |
| API6 | Unrestricted Access to Sensitive Business Flows | 100 swipes per day limit. 1 message per second cooldown. Application-level business rule enforcement in the service layer. | `app/services/swipe_service.py`, `app/services/message_service.py`, `tests/security/test_business_flow.py` |
| API7 | Server Side Request Forgery | Image URL domain allowlist (imgur, unsplash, cloudinary, S3). DNS resolution checked against private IP ranges. Blocks: 10.x, 172.16.x, 192.168.x, 127.x, 169.254.x (AWS metadata), IPv6 private. | `app/core/url_validator.py`, `tests/security/test_ssrf.py` |
| API8 | Security Misconfiguration | Explicit CORS origins (never `*`). Security headers on all responses (X-Content-Type-Options, X-Frame-Options, HSTS, CSP). Generic error messages with no stack traces. `/docs` disabled in production. Environment-based configuration. | `app/core/middleware.py`, `app/core/exceptions.py`, `tests/security/test_misconfiguration.py` |
| API9 | Improper Inventory Management | All endpoints under `/api/v1/`. No shadow or deprecated routes. Auto-generated OpenAPI spec with descriptions. | `app/api/v1/router.py`, `tests/security/test_inventory.py` |
| API10 | Unsafe Consumption of APIs | 5-second timeout on external URL validation requests. External Content-Type headers not trusted for security decisions. Response size limits on HEAD requests. | `app/core/url_validator.py`, `app/services/photo_service.py` |

## API Endpoints

All endpoints are under `/api/v1/`.

### Authentication
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | None | Create account (rate limited: 5/min) |
| POST | `/auth/login` | None | Get tokens (rate limited: 10/min, lockout after 5 failures) |
| POST | `/auth/refresh` | Refresh token | Rotate tokens |
| POST | `/auth/logout` | Bearer | Revoke refresh token |
| POST | `/auth/password-reset/request` | None | Request reset (generic response) |
| POST | `/auth/password-reset/confirm` | Reset token | Set new password |

### Users
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/users/me` | Bearer | Get own profile |
| PATCH | `/users/me` | Bearer | Update own profile |
| DELETE | `/users/me` | Bearer | Deactivate account |

### Horses
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/horses/` | Bearer | Create horse (max 5 per user) |
| GET | `/horses/` | Bearer | List own horses |
| GET | `/horses/{id}` | Bearer | Get horse details |
| PATCH | `/horses/{id}` | Bearer | Update horse (ownership required) |
| DELETE | `/horses/{id}` | Bearer | Soft-delete horse (ownership required) |

### Horse Photos
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/horses/{id}/photos/` | Bearer | Add photo URL (SSRF validated, max 10) |
| GET | `/horses/{id}/photos/` | Bearer | List photos |
| PATCH | `/horses/{id}/photos/{photo_id}` | Bearer | Update photo order/primary |
| DELETE | `/horses/{id}/photos/{photo_id}` | Bearer | Delete photo |

### Swipes & Matches
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/swipes/` | Bearer | Like or pass (100/day limit) |
| GET | `/swipes/remaining` | Bearer | Check remaining daily swipes |
| GET | `/matches/` | Bearer | List matches |
| GET | `/matches/{id}` | Bearer | Match details |
| DELETE | `/matches/{id}` | Bearer | Unmatch |

### Messages
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/matches/{id}/messages/` | Bearer | List messages (match membership required) |
| POST | `/matches/{id}/messages/` | Bearer | Send message (1/sec cooldown) |
| PATCH | `/matches/{id}/messages/{msg_id}/read` | Bearer | Mark as read |

### Notifications
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/notifications/` | Bearer | List notifications |
| PATCH | `/notifications/{id}/read` | Bearer | Mark as read |
| POST | `/notifications/read-all` | Bearer | Mark all as read |

### Search
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/search/horses` | Bearer | Filter by breed, age, location, temperament |

### Admin
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/admin/users` | Admin | List all users |
| GET | `/admin/users/{id}` | Admin | User detail (extended fields) |
| PATCH | `/admin/users/{id}` | Admin | Update user (lock, role, active) |
| DELETE | `/admin/users/{id}` | Admin | Delete user |
| GET | `/admin/horses` | Admin | List all horses |
| PATCH | `/admin/horses/{id}` | Admin | Moderate horse |

## Database Schema

All tables use UUID primary keys to prevent enumeration (OWASP API1).

```
users             1--* horses           1--* horse_photos
  |                     |     |
  |                     |     +--* swipes
  |                     |
  +--* refresh_tokens   +--* matches --* messages
  +--* login_attempts   
  +--* notifications
```

## Testing

```bash
# Run all tests (154 tests)
pytest tests/ -v

# Run by category
pytest tests/unit/ -v          # Schema validation, JWT, SSRF validator
pytest tests/integration/ -v   # Full API flow tests
pytest tests/security/ -v      # OWASP security tests (9 files, one per item)

# With coverage
pytest tests/ --cov=app --cov-report=term-missing
```

### Security Test Coverage

Each OWASP item has a dedicated test file in `tests/security/` that verifies the mitigation with concrete attack scenarios:

- `test_bola.py` -- Cross-user resource access attempts (8 tests)
- `test_auth_security.py` -- Brute force, token manipulation, account lockout (7 tests)
- `test_property_auth.py` -- Mass assignment, data leakage prevention (7 tests)
- `test_resource_limits.py` -- Pagination abuse, body size limits (6 tests)
- `test_function_auth.py` -- Non-admin accessing admin endpoints (8 tests)
- `test_business_flow.py` -- Swipe flooding, message spam (2 tests)
- `test_ssrf.py` -- Private IP, metadata endpoint, scheme abuse (13 tests)
- `test_misconfiguration.py` -- Error exposure, security headers, info leaks (9 tests)
- `test_inventory.py` -- Shadow API detection, versioning (5 tests)

## Project Structure

```
app/
  core/           # Security, config, middleware, rate limiting, SSRF validator
  models/         # SQLAlchemy models with UUID PKs
  schemas/        # Pydantic schemas (separate Create/Update/Read per API3)
  api/v1/         # Route handlers under /api/v1/ (API9)
  services/       # Business logic with ownership checks (API1)
  db/             # Async session factory
tests/
  unit/           # Schema validation, JWT, URL validator
  integration/    # Full API flow tests
  security/       # One file per OWASP Top 10 item
```

## Production Considerations

This project demonstrates the patterns. For production deployment, additionally consider:

- **HTTPS termination** via reverse proxy (nginx/Caddy)
- **Secrets management** via HashiCorp Vault or cloud KMS
- **Redis** for rate limit storage across multiple workers
- **Database encryption at rest** and connection pooling (PgBouncer)
- **Audit logging** for security-sensitive operations
- **Multi-factor authentication** for admin accounts
- **CAPTCHA** integration for registration and password reset
- **API key rotation** policies

## License

MIT
