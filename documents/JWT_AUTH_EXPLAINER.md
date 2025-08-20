# JWT Authentication — A DevOps‑Oriented Explainer

This document explains JSON Web Tokens (JWT) in practical, production‑focused terms, then maps those concepts to this codebase.

## What JWT is (and why it’s used)
- **JWT** is a compact, signed token that encodes claims (facts) about a subject (typically a user).
- **Stateless**: the server can validate a token without a session store.
- **Typical use**: short‑lived access tokens for APIs; optionally paired with a long‑lived refresh token.

## Token structure
A JWT is three Base64URL parts joined with dots: `header.payload.signature`

- **Header**: algorithm and type, e.g. `{ "alg": "HS256", "typ": "JWT" }`
- **Payload (claims)**: facts like `sub` (user id), `exp` (expiry), `iat` (issued‑at), `nbf` (not‑before), `iss` (issuer), `aud` (audience)
- **Signature**: cryptographic signature over header+payload using the server’s secret key or private key

Common claims:
- **sub**: subject (user id)
- **exp**: expiration time (UNIX timestamp)
- **iat/nbf**: issued‑at / not‑before
- **iss/aud**: issuer/audience (recommended in larger systems)
- **jti**: unique token id (useful for revocation lists)

## High‑level flow
1. Client authenticates once (username/password) to receive an **access token**.
2. Client sends the token on subsequent requests: `Authorization: Bearer <token>`.
3. API **verifies the signature** and **validates claims** (e.g., `exp`, `nbf`, `iss`, `aud`).
4. If valid, the request runs as that user; otherwise, it’s rejected (401/403).

## How it works in this codebase
- Login returns a signed JWT with `sub=<user_id>` and an 8‑day expiry.
- Clients store the token (here: `localStorage`) and send it via `Authorization: Bearer`.
- FastAPI dependency extracts and verifies the token, loads the current user from DB, and enforces role checks.

Relevant code (simplified):
```python
# backend/app/core/security/jwt.py
from jose import jwt

def create_access_token(subject, expires_delta=None):
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> Optional[str]:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])  # raises on invalid/expired
    return payload["sub"]
```
```python
# backend/app/dependencies/auth.py
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user_id = verify_token(token)
    user = await user_repo.get(db, id=int(user_id))
    ...
    return user
```

## Symmetric vs. asymmetric signing
- **HS256 (HMAC)**: shared secret; simple and fast. Protect `SECRET_KEY`; rotate periodically.
- **RS256/ES256 (asymmetric)**: private key signs, public key verifies. Better for multi‑service verification and key rotation via JWKS.

## Where to store the token (browser)
- **localStorage**: simple; vulnerable to XSS. If used, emphasize XSS hardening.
- **HttpOnly Secure SameSite cookies**: not readable by JS (mitigates XSS); consider CSRF protections (SameSite=Lax/Strict and/or CSRF token).

## Expiration and refresh strategy
- Keep **access tokens short‑lived** (e.g., 5–15 minutes) for reduced blast radius.
- Use **refresh tokens** (long‑lived, stored more securely) to mint new access tokens.
- This repo currently uses an **8‑day access token without refresh**; consider adding refresh rotation for production.

## Revocation and logout options
JWTs are stateless; you can’t retract an already issued token unless you:
- Rely on **short TTL** and let them expire, or
- Maintain a **denylist** keyed by `jti`/user/version, or
- **Rotate keys** (mass revocation), or
- Track a per‑user **token version** in DB and include it in token claims.

## Common pitfalls
- Long‑lived access tokens without refresh.
- Weak `SECRET_KEY` or exposing it in logs/configs.
- Accepting tokens without checking `exp`/`nbf`/`aud`/`iss`.
- Not enforcing **TLS everywhere**.
- Storing tokens where XSS can access them; insufficient input sanitization.
- Algorithm confusion attacks: always specify the allowed algorithms.

## Operational guidance (DevOps)
- **Secrets management**: inject `SECRET_KEY` from a secret store (Kubernetes Secrets, AWS SM, Vault). Rotate on schedule.
- **Key rotation**:
  - HS256: window that accepts old+new secrets until cutover.
  - RS256/ES256: publish **JWKS** and rotate keys with `kid` identifiers.
- **Observability**:
  - Metrics: counts of 401/403, invalid signature, expired token, rate‑limit rejections.
  - Logs: auth failure reasons (no token, invalid, expired, audience/issuer mismatch).
- **Time sync**: NTP for accurate `exp/nbf` validation.
- **Rate limiting**: keep stricter limits on auth endpoints (this repo uses SlowAPI).
- **CORS/TLS**: enforce HTTPS; configure CORS carefully for browsers.
- **Token size**: keep claims minimal; never put secrets in payload (payload is only encoded, not encrypted).
- **Blue/green/rolling**: ensure all instances can validate old+new keys during rotations.

## Example usage
```bash
# 1) Login to get access token
curl -X POST http://localhost:8000/api/v1/users/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=StrongPass123"

# 2) Call an authenticated endpoint with the token
curl http://localhost:8000/api/v1/chores \
  -H "Authorization: Bearer eyJhbGciOi..."
```

## Production hardening checklist
- Shorten access token TTL; add **refresh tokens** with rotation and `jti`.
- Prefer **HttpOnly Secure SameSite cookies** (or heavily harden XSS if using localStorage).
- Validate **exp/nbf/iss/aud**; include `kid` for key rotation; consider **RS256** with JWKS if multiple verifiers.
- Centralize secrets; **rotate** on a schedule; alert on verification anomaly spikes.
- Strong rate limits + bot protection on login/register.
- Consider **per‑user token versioning** to support targeted revocation.

## Repo‑specific notes
- Signing: **HS256** with `settings.SECRET_KEY`; claims include `sub` and `exp`; default expiry is **8 days**.
- Verification is done per request via dependency injection (`get_current_user`).
- Web UI stores token in `localStorage` and adds `Authorization` header on HTMX/fetch requests.

## Suggested next steps
- Add a **refresh‑token flow** (HttpOnly cookie) and shorten access token TTL.
- Add `iss/aud/jti` claims and per‑user token version for targeted revocation.
- Consider migrating to **RS256 + JWKS** for safer rotations across services.
- Move `SECRET_KEY` to a managed secret and formalize a rotation runbook.
