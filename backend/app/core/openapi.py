"""Custom OpenAPI schema modifications for better documentation."""
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from typing import Dict, Any


def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """Generate custom OpenAPI schema with enhanced documentation."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
        servers=app.servers,
    )
    
    # Add API version information
    openapi_schema["info"]["x-api-versions"] = {
        "v1": {
            "status": "stable",
            "deprecated": False,
            "description": "Legacy API with mixed JSON/HTML responses"
        },
        "v2": {
            "status": "stable", 
            "deprecated": False,
            "description": "Modern JSON-only API with standardized responses"
        }
    }
    
    # Add authentication details
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from /api/v2/auth/login endpoint"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"bearerAuth": []}]
    
    # Add server information
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Local development server"
        },
        {
            "url": "https://api.chores-tracker.com",
            "description": "Production server"
        }
    ]
    
    # Add example responses for common scenarios
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    openapi_schema["components"]["examples"] = {
        "UnauthorizedError": {
            "value": {
                "success": False,
                "data": None,
                "error": "Not authenticated",
                "timestamp": "2024-01-28T10:00:00Z"
            }
        },
        "ForbiddenError": {
            "value": {
                "success": False,
                "data": None,
                "error": "Not authorized to perform this action",
                "timestamp": "2024-01-28T10:00:00Z"
            }
        },
        "NotFoundError": {
            "value": {
                "success": False,
                "data": None,
                "error": "Resource not found",
                "timestamp": "2024-01-28T10:00:00Z"
            }
        },
        "ValidationError": {
            "value": {
                "success": False,
                "data": None,
                "error": "Validation error",
                "timestamp": "2024-01-28T10:00:00Z"
            }
        },
        "RateLimitError": {
            "value": {
                "detail": "Rate limit exceeded: 5 per 1 minute"
            }
        }
    }
    
    # Add webhook information (for future use)
    openapi_schema["webhooks"] = {
        "choreCompleted": {
            "post": {
                "requestBody": {
                    "description": "Notification when a chore is completed",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ChoreResponse"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Webhook processed successfully"
                    }
                }
            }
        }
    }
    
    # Enhance specific endpoint documentation
    paths = openapi_schema.get("paths", {})
    
    # Enhance v2 login endpoint
    if "/api/v2/auth/login" in paths:
        paths["/api/v2/auth/login"]["post"]["x-code-samples"] = [
            {
                "lang": "curl",
                "source": """curl -X POST http://localhost:8000/api/v2/auth/login \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -d "username=parent_user&password=SecurePassword123" """
            },
            {
                "lang": "JavaScript",
                "source": """const formData = new URLSearchParams();
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
const token = data.data.access_token;"""
            }
        ]
    
    # Enhance v2 create chore endpoint
    if "/api/v2/chores/" in paths and "post" in paths["/api/v2/chores/"]:
        paths["/api/v2/chores/"]["post"]["x-code-samples"] = [
            {
                "lang": "curl",
                "source": """curl -X POST http://localhost:8000/api/v2/chores/ \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "title": "Clean Room",
    "description": "Make bed, vacuum, organize toys",
    "reward": 5.0,
    "assignee_id": 2,
    "cooldown_days": 7,
    "is_recurring": true
  }'"""
            },
            {
                "lang": "Python",
                "source": """import requests

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
)"""
            }
        ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema