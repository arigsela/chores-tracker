# JWT Authentication Guide

## Overview

The Chores Tracker API uses **JWT (JSON Web Token)** authentication for securing endpoints. This guide provides comprehensive information for developers integrating with the API.

### Key Facts

- **Token Type**: JWT (JSON Web Token)
- **Algorithm**: HS256 (HMAC with SHA-256)
- **Token Expiration**: 8 days (11,520 minutes)
- **Token Format**: Bearer token in Authorization header
- **Password Hashing**: bcrypt
- **OAuth2 Flow**: Password grant type

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Login Flow](#login-flow)
3. [Token Structure](#token-structure)
4. [Using Tokens in Requests](#using-tokens-in-requests)
5. [Role-Based Access Control](#role-based-access-control)
6. [Token Expiration and Refresh](#token-expiration-and-refresh)
7. [Frontend Integration Examples](#frontend-integration-examples)
8. [Testing Authentication](#testing-authentication)
9. [Common Errors and Solutions](#common-errors-and-solutions)
10. [Security Best Practices](#security-best-practices)

---

## Quick Start

### 1. Login to Get Token

```bash
curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=parent_user&password=secure_password"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzI3NDg4MDAsInN1YiI6IjEifQ.xYz123...",
  "token_type": "bearer"
}
```

### 2. Use Token in Subsequent Requests

```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## Login Flow

### Endpoint: `POST /api/v1/users/login`

The login endpoint follows the **OAuth2 Password Flow** and expects form-encoded credentials.

#### Request Format

**Headers:**
```
Content-Type: application/x-www-form-urlencoded
```

**Body (form-encoded):**
```
username=parent_user&password=secure_password
```

#### Complete curl Example

```bash
curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=parent_user" \
  -d "password=secure_password"
```

#### Success Response (200 OK)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzI3NDg4MDAsInN1YiI6IjEifQ.xYz123abc...",
  "token_type": "bearer"
}
```

#### Error Responses

**Invalid Credentials (401 Unauthorized):**
```json
{
  "detail": "Invalid username or password"
}
```

**Inactive User (401 Unauthorized):**
```json
{
  "detail": "User is inactive"
}
```

**Rate Limit Exceeded (429 Too Many Requests):**
```json
{
  "detail": "Too Many Requests"
}
```

**Rate Limits:**
- Login endpoint: 5 requests per minute per IP
- Registration endpoint: 3 requests per minute per IP

---

## Token Structure

### JWT Claims

A decoded JWT token contains the following claims:

```json
{
  "exp": 1732748800,    // Expiration timestamp (Unix epoch)
  "sub": "1"            // Subject: User ID as string
}
```

#### Claim Details

- **`exp`** (Expiration Time): Unix timestamp when the token expires (8 days from issuance)
- **`sub`** (Subject): User ID as a string (e.g., "1", "42")

### Decoding Example (Python)

```python
from jose import jwt

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
secret_key = "your_secret_key"  # From settings.SECRET_KEY

try:
    payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    user_id = payload["sub"]
    expiration = payload["exp"]
    print(f"User ID: {user_id}, Expires: {expiration}")
except jwt.JWTError:
    print("Invalid token")
```

### Token Creation (Backend Reference)

The backend creates tokens using this logic:

```python
# backend/app/core/security/jwt.py
from datetime import datetime, timedelta
from jose import jwt
from ...core.config import settings

def create_access_token(subject: Any, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES  # 11,520 minutes = 8 days
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt
```

---

## Using Tokens in Requests

### Authorization Header Format

All authenticated requests must include the JWT token in the `Authorization` header:

```
Authorization: Bearer <token>
```

### curl Examples

**Get Current User Profile:**
```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Create a Chore (Parent Only):**
```bash
curl -X POST "http://localhost:8000/api/v1/chores/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Mow the lawn",
    "description": "Front and back yard",
    "reward": 15.0,
    "assignment_mode": "single",
    "assignee_ids": [2]
  }'
```

**Get Available Chores (Child):**
```bash
curl -X GET "http://localhost:8000/api/v1/chores/available" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Backend Token Verification

The backend verifies tokens using FastAPI dependencies:

```python
# backend/app/dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user."""
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await user_repo.get(db, id=int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
```

---

## Role-Based Access Control

The API has two user roles: **Parent** and **Child**.

### User Roles

| Role   | Permissions                                                  |
|--------|--------------------------------------------------------------|
| Parent | Create/manage chores, approve completions, manage children, view all family data |
| Child  | View assigned chores, mark complete, view own balance       |

### Parent-Only Endpoints

These endpoints require the authenticated user to be a parent:

```python
async def get_current_parent(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get the current authenticated user, ensuring they are a parent."""
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires parent privileges"
        )
    return current_user
```

**Examples:**
- `POST /api/v1/chores/` - Create chores
- `POST /api/v1/assignments/{assignment_id}/approve` - Approve completions
- `POST /api/v1/users/children/{child_id}/reset-password` - Reset child passwords
- `GET /api/v1/users/my-children` - List children
- `GET /api/v1/users/allowance-summary` - View allowance summary

### Child Endpoints

Children can access:
- `GET /api/v1/chores/available` - View available chores
- `POST /api/v1/chores/{chore_id}/complete` - Mark chores complete
- `GET /api/v1/users/me` - View own profile

### Family Context

The API supports family-based access control:

```python
async def require_family_membership(
    user_with_family: UserWithFamily = Depends(get_current_user_with_family)
) -> UserWithFamily:
    """Ensure the current user belongs to a family."""
    if not user_with_family.family:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires family membership. Please create or join a family first."
        )
    return user_with_family
```

---

## Token Expiration and Refresh

### Token Expiration

- **Default Expiration**: 8 days (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Configuration**: Set in `backend/app/core/config.py`

```python
# backend/app/core/config.py
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 8)  # 8 days
)
```

### Environment Variable Override

You can customize token expiration in your `.env` file:

```bash
# .env
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days
# or
ACCESS_TOKEN_EXPIRE_MINUTES=1440   # 1 day
```

### Token Refresh Strategy

**Current Implementation**: No automatic token refresh

The API currently does not implement automatic token refresh. When a token expires:

1. The client receives a `401 Unauthorized` response
2. The client should redirect to the login page
3. User re-authenticates to get a new token

**Future Enhancement**: Implement refresh tokens for seamless re-authentication.

### Checking Token Expiration

**Frontend Example (JavaScript):**

```javascript
function isTokenExpired(token) {
  try {
    // Decode JWT (without verification - just read claims)
    const payload = JSON.parse(atob(token.split('.')[1]));
    const expirationDate = new Date(payload.exp * 1000);
    return expirationDate < new Date();
  } catch (error) {
    return true;  // Invalid token
  }
}

// Usage
const token = localStorage.getItem('access_token');
if (isTokenExpired(token)) {
  // Redirect to login
  window.location.href = '/login';
}
```

### Handling Expired Tokens

**Recommended Flow:**

1. Store token in secure storage (localStorage, sessionStorage, or cookies)
2. Include token in all API requests
3. Handle `401 Unauthorized` responses by redirecting to login
4. Clear stored token on logout

---

## Frontend Integration Examples

### JavaScript/TypeScript (Axios)

```typescript
import axios from 'axios';

// Configure axios instance
const apiClient = axios.create({
  baseURL: process.env.NODE_ENV === 'development'
    ? 'http://localhost:8000/api/v1'
    : '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add authentication interceptor
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle authentication errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Login function
async function login(username: string, password: string) {
  try {
    const response = await axios.post(
      'http://localhost:8000/api/v1/users/login',
      new URLSearchParams({ username, password }),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    const { access_token } = response.data;
    localStorage.setItem('access_token', access_token);
    return access_token;
  } catch (error) {
    console.error('Login failed:', error);
    throw error;
  }
}

// Example API call
async function getCurrentUser() {
  const response = await apiClient.get('/users/me');
  return response.data;
}
```

### React Native (Frontend Implementation)

```typescript
// frontend/src/contexts/AuthContext.tsx
import React, { createContext, useState, useContext } from 'react';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface AuthContextType {
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);

  const login = async (username: string, password: string) => {
    try {
      const response = await axios.post(
        'http://localhost:8000/api/v1/users/login',
        new URLSearchParams({ username, password }),
        {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        }
      );

      const { access_token } = response.data;
      await AsyncStorage.setItem('access_token', access_token);
      setToken(access_token);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const logout = async () => {
    await AsyncStorage.removeItem('access_token');
    setToken(null);
  };

  return (
    <AuthContext.Provider value={{
      token,
      login,
      logout,
      isAuthenticated: !!token,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

### Python (requests library)

```python
import requests

# Login
def login(username: str, password: str) -> str:
    """Login and return JWT token."""
    response = requests.post(
        "http://localhost:8000/api/v1/users/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    response.raise_for_status()
    return response.json()["access_token"]

# Make authenticated request
def get_current_user(token: str):
    """Get current user profile."""
    response = requests.get(
        "http://localhost:8000/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    response.raise_for_status()
    return response.json()

# Usage
token = login("parent_user", "secure_password")
user = get_current_user(token)
print(f"Logged in as: {user['username']}")
```

---

## Testing Authentication

### Development Environment

#### 1. Create a Test User

```bash
# Using Docker Compose
docker compose exec api python -m backend.app.scripts.create_parent_user

# Or using the API
curl -X POST "http://localhost:8000/api/v1/users/register" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test_parent" \
  -d "password=password123" \
  -d "email=test@example.com" \
  -d "is_parent=true" \
  -d "registration_code=BETA2024"
```

#### 2. Login and Get Token

```bash
curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test_parent&password=password123"
```

**Save the token:**
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### 3. Test Authenticated Endpoints

```bash
# Get current user
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer $TOKEN"

# Create a child user
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_child",
    "password": "childpass",
    "is_parent": false
  }'

# Get children
curl -X GET "http://localhost:8000/api/v1/users/my-children" \
  -H "Authorization: Bearer $TOKEN"
```

### Using FastAPI Interactive Docs

The API includes automatic interactive documentation:

1. **Navigate to**: http://localhost:8000/docs
2. **Click "Authorize"** button (top right)
3. **Login flow**:
   - Scroll to `POST /api/v1/users/login`
   - Click "Try it out"
   - Enter username and password
   - Click "Execute"
   - Copy the `access_token` from the response
4. **Authorize**:
   - Click "Authorize" button again
   - Paste token in the "Value" field
   - Click "Authorize"
5. **Test endpoints** with the authenticated token

### Automated Testing

**Python pytest example:**

```python
# backend/tests/test_authentication.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login returns token."""
    response = await client.post(
        "/api/v1/users/login",
        data={"username": "test_user", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with invalid credentials fails."""
    response = await client.post(
        "/api/v1/users/login",
        data={"username": "test_user", "password": "wrong_password"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"

@pytest.mark.asyncio
async def test_authenticated_endpoint(client: AsyncClient, auth_headers):
    """Test accessing protected endpoint with valid token."""
    response = await client.get(
        "/api/v1/users/me",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "username" in data

@pytest.mark.asyncio
async def test_unauthenticated_access(client: AsyncClient):
    """Test accessing protected endpoint without token fails."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401
```

---

## Common Errors and Solutions

### 401 Unauthorized

**Error:**
```json
{
  "detail": "Invalid authentication credentials"
}
```

**Causes:**
1. Token is missing
2. Token is malformed
3. Token has expired
4. Token signature is invalid
5. User account is inactive

**Solutions:**
```bash
# Check token format
echo "Authorization: Bearer <token>"  # Must start with "Bearer "

# Verify token is not expired
# Decode JWT and check 'exp' claim

# Re-login to get fresh token
curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_user&password=your_password"
```

### 403 Forbidden

**Error:**
```json
{
  "detail": "This operation requires parent privileges"
}
```

**Cause:** User lacks required role (e.g., child trying to access parent-only endpoint)

**Solution:** Ensure you're logged in as the correct user role.

### 429 Too Many Requests

**Error:**
```json
{
  "detail": "Too Many Requests"
}
```

**Cause:** Rate limit exceeded

**Rate Limits:**
- Login: 5 requests/minute
- Registration: 3 requests/minute
- Default API endpoints: 100 requests/minute

**Solution:** Wait 60 seconds and retry.

### Missing Authorization Header

**Error:**
```json
{
  "detail": "Not authenticated"
}
```

**Cause:** Request missing `Authorization` header

**Solution:**
```bash
# Add Authorization header to all authenticated requests
-H "Authorization: Bearer <token>"
```

### Invalid Token Format

**Error:**
```json
{
  "detail": "Invalid authentication credentials"
}
```

**Common Mistakes:**
```bash
# Wrong - missing "Bearer " prefix
-H "Authorization: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Correct
-H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Token Expired

**Symptoms:**
- Previously working token returns 401
- Error: "Invalid authentication credentials"

**Solution:**
```bash
# Re-login to get fresh token
curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_user&password=your_password"
```

---

## Security Best Practices

### 1. Store Tokens Securely

**Don't:**
- Store tokens in browser localStorage (vulnerable to XSS)
- Log tokens to console
- Include tokens in URLs
- Commit tokens to version control

**Do:**
- Use httpOnly cookies when possible
- Use secure, same-site cookies in production
- Clear tokens on logout
- Implement token rotation

### 2. Use HTTPS in Production

```bash
# Production: Always use HTTPS
https://api.yourdomain.com/api/v1/users/login

# Development: HTTP is acceptable for localhost
http://localhost:8000/api/v1/users/login
```

### 3. Handle Token Expiration Gracefully

```typescript
// Automatically redirect to login on 401
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### 4. Validate Token Before Using

```javascript
function isValidToken(token) {
  if (!token) return false;

  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const now = Date.now() / 1000;
    return payload.exp > now;
  } catch {
    return false;
  }
}
```

### 5. Use Strong Passwords

- Minimum 8 characters for parents
- Minimum 4 characters for children
- Consider implementing password strength requirements

### 6. Rate Limiting

The API implements rate limiting to prevent brute-force attacks:

```python
# backend/app/middleware/rate_limit.py
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@limiter.limit("5/minute")  # Login endpoint
async def login(...):
    ...

@limiter.limit("3/minute")  # Registration endpoint
async def register_user(...):
    ...
```

### 7. Environment-Specific Configuration

```bash
# .env (development)
SECRET_KEY=development_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=11520  # 8 days
DEBUG=True

# .env.production
SECRET_KEY=<strong-random-secret-key>
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 1 day for production
DEBUG=False
```

### 8. Monitor for Suspicious Activity

Watch for:
- Multiple failed login attempts
- Token reuse after logout
- Requests from unexpected IP addresses
- Unusual request patterns

---

## Configuration Reference

### Environment Variables

```bash
# backend/.env

# JWT Configuration
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=11520  # 8 days (default)

# CORS Origins (comma-separated)
BACKEND_CORS_ORIGINS=http://localhost:8081,http://localhost:3000

# Registration Codes (Beta Feature)
REGISTRATION_CODES=BETA2024,FAMILY_TRIAL,CHORES_BETA
```

### Backend Configuration

```python
# backend/app/core/config.py
class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "development_secret_key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 8)  # 8 days
    )
```

---

## API Endpoints Reference

### Authentication Endpoints

| Method | Endpoint                  | Auth Required | Role    | Description                    |
|--------|---------------------------|---------------|---------|--------------------------------|
| POST   | `/api/v1/users/login`     | No            | -       | Login and get JWT token        |
| POST   | `/api/v1/users/register`  | No            | -       | Register new user (with code)  |
| GET    | `/api/v1/users/me`        | Yes           | Any     | Get current user profile       |

### User Management Endpoints

| Method | Endpoint                           | Auth Required | Role   | Description                    |
|--------|-------------------------------------|---------------|--------|--------------------------------|
| GET    | `/api/v1/users/`                   | Yes           | Any    | List all users (paginated)     |
| POST   | `/api/v1/users/`                   | Yes           | Parent | Create new user (JSON API)     |
| GET    | `/api/v1/users/my-children`        | Yes           | Parent | Get children for current parent|
| GET    | `/api/v1/users/children/{parent_id}`| Yes          | Any    | Get children for specific parent|
| POST   | `/api/v1/users/children/{child_id}/reset-password` | Yes | Parent | Reset child's password    |
| GET    | `/api/v1/users/allowance-summary`  | Yes           | Parent | Get allowance summary          |

### Rate Limits

- **Login**: 5 requests per minute
- **Registration**: 3 requests per minute
- **Other endpoints**: 100 requests per minute

---

## Troubleshooting Checklist

- [ ] Verify token includes "Bearer " prefix
- [ ] Check token has not expired (8-day default)
- [ ] Ensure Content-Type header is correct for login (application/x-www-form-urlencoded)
- [ ] Confirm user account is active
- [ ] Verify correct role for endpoint (parent vs child)
- [ ] Check rate limits haven't been exceeded
- [ ] Ensure CORS origins are configured for frontend domain
- [ ] Test with curl before implementing in client
- [ ] Check backend logs for detailed error messages

---

## Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **OpenAPI Spec**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/api/v1/health
- **Repository**: [Project README](/Users/arisela/git/chores-tracker/README.md)

---

**Last Updated**: 2025-11-23
**API Version**: 3.0.0
