# API Endpoint Template

# Endpoint Name

## Overview
Brief description of what this endpoint does.

## Endpoint
```http
METHOD /path/to/endpoint
```

## Authentication
- Required: Yes/No
- Type: Bearer Token/API Key/None
- Scope: Required permissions

## Request

### Headers
```http
Authorization: Bearer <token>
Content-Type: application/json
```

### Parameters
| Name | Type | Required | Description |
|------|------|----------|-------------|
| param1 | string | Yes | Description of param1 |
| param2 | integer | No | Description of param2 |

### Request Body
```json
{
    "field1": "value1",
    "field2": 123
}
```

## Response

### Success Response
```json
{
    "status": "success",
    "data": {
        "field1": "value1",
        "field2": 123
    }
}
```

### Error Response
```json
{
    "status": "error",
    "error": {
        "code": "ERROR_CODE",
        "message": "Error description"
    }
}
```

## Rate Limiting
- Requests per minute: X
- Requests per hour: Y

## Examples

### cURL
```bash
curl -X METHOD \
  'https://api.example.com/endpoint' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "field1": "value1",
    "field2": 123
  }'
```

### Python
```python
import requests

response = requests.method(
    'https://api.example.com/endpoint',
    headers={
        'Authorization': 'Bearer <token>',
        'Content-Type': 'application/json'
    },
    json={
        'field1': 'value1',
        'field2': 123
    }
)
```

## Notes
- Additional information about the endpoint
- Known limitations
- Best practices

## Related
- Links to related endpoints
- References to external documentation
