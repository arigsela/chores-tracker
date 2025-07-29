# OpenAPI v2 Documentation Updates

## Overview
The OpenAPI documentation has been enhanced to provide comprehensive API documentation for both v1 and v2 endpoints, with a focus on the new standardized v2 API.

## Key Enhancements

### 1. Updated Main Documentation
- Added clear distinction between v1 (Legacy) and v2 (Recommended) APIs
- Included standardized response format examples
- Enhanced authentication flow documentation
- Added code examples for common operations

### 2. Enhanced Response Schemas
All response schemas now include multiple examples:

#### ApiResponse
- Success example with data
- Error example without data
- Timestamp included in all responses

#### PaginatedResponse
- Realistic chore list example
- Pagination metadata (page, page_size, total, total_pages)

#### ErrorResponse
- Multiple error scenarios (unauthorized, validation, not found)
- Error codes for programmatic handling
- Detailed error information

### 3. Custom OpenAPI Schema
Created `/backend/app/core/openapi.py` with:
- API version information
- Security scheme definitions (Bearer JWT)
- Server configurations (dev/prod)
- Common error response examples
- Code samples for key endpoints
- Webhook definitions (future use)

### 4. Enhanced Schema Examples

#### ChoreCreate
- Fixed reward example
- Range-based reward example
- Recurring chore configurations

#### ChoreApprove
- Examples for both fixed and range rewards
- Clear documentation of when reward_value is required

#### User Schemas
- Parent registration example
- Child registration example
- Comprehensive field descriptions

### 5. OpenAPI Tags
Organized endpoints with clear tags:
- `auth-v2`: Authentication endpoints (v2)
- `users-v2`: User management (v2) 
- `chores-v2`: Chore management (v2)
- `users`: Legacy v1 user endpoints
- `chores`: Legacy v1 chore endpoints
- `html`: HTMX-specific endpoints

## Accessing the Documentation

### Swagger UI
- URL: http://localhost:8000/docs
- Interactive API testing
- Try-it-out functionality
- Authentication support

### ReDoc
- URL: http://localhost:8000/redoc
- Clean, readable documentation
- Better for sharing/printing

### OpenAPI JSON
- URL: http://localhost:8000/api/v1/openapi.json
- Machine-readable specification
- Can be imported into Postman/Insomnia

## Code Samples Added

### Login Example (cURL)
```bash
curl -X POST http://localhost:8000/api/v2/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=parent_user&password=SecurePassword123"
```

### Login Example (JavaScript)
```javascript
const formData = new URLSearchParams();
formData.append('username', 'parent_user');
formData.append('password', 'SecurePassword123');

const response = await fetch('http://localhost:8000/api/v2/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: formData
});

const data = await response.json();
const token = data.data.access_token;
```

### Create Chore Example (Python)
```python
import requests

headers = {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
}

data = {
    'title': 'Clean Room',
    'description': 'Make bed, vacuum, organize toys',
    'reward': 5.0,
    'assignee_id': 2,
    'cooldown_days': 7,
    'is_recurring': True
}

response = requests.post(
    'http://localhost:8000/api/v2/chores/',
    headers=headers,
    json=data
)
```

## Benefits for Frontend Developers

1. **Clear API Contract** - Exact request/response formats
2. **Interactive Testing** - Try endpoints directly in browser
3. **Code Generation** - Can generate client SDKs
4. **Type Safety** - Schema definitions for TypeScript
5. **Examples** - Multiple realistic examples per endpoint

## Next Steps

1. **Generate TypeScript Types** - Use openapi-typescript generator
2. **Create Postman Collection** - Export from OpenAPI spec
3. **Add More Examples** - Cover edge cases
4. **API Client Libraries** - Generate for React/mobile
5. **Versioning Strategy** - Document deprecation timeline

## Testing the Documentation

1. Start the API:
   ```bash
   docker compose up -d
   ```

2. Access Swagger UI:
   ```
   http://localhost:8000/docs
   ```

3. Test authentication:
   - Use "Authorize" button
   - Enter JWT token
   - Test protected endpoints

4. Export for team:
   ```bash
   curl http://localhost:8000/api/v1/openapi.json > openapi-spec.json
   ```

The enhanced OpenAPI documentation provides a solid foundation for frontend development and API integration.