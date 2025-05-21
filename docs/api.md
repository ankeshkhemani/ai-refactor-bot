# API Documentation

## Overview

The AI Refactoring Bot API is built with FastAPI and provides endpoints for GitHub webhook integration and health checks.

## Base URL

```
https://your-domain.com
```

## Authentication

The API uses GitHub App authentication:
- JWT tokens for GitHub App authentication
- Installation access tokens for repository access
- Webhook secret for event verification

## Endpoints

### Health Check

```http
GET /ping
```

Checks if the service is running.

**Response**:
```json
{
    "status": "ok",
    "message": "pong"
}
```

### GitHub Webhook

```http
POST /webhook
```

Handles GitHub webhook events.

**Headers Required**:
- `X-GitHub-Event`: The type of GitHub event
- `X-GitHub-Delivery`: Unique identifier for the event
- `X-Hub-Signature`: HMAC hex digest of the payload

**Event Types**:
1. `installation` - GitHub App installation events
2. `pull_request` - Pull request events
3. `push` - Push events

**Example Installation Event**:
```json
{
    "action": "created",
    "installation": {
        "id": 12345678,
        "account": {
            "login": "username"
        },
        "repository_selection": "selected",
        "repositories": [
            {
                "id": 11111111,
                "name": "example-repo"
            }
        ]
    }
}
```

**Response**:
```json
{
    "status": "success",
    "event": "installation"
}
```

## Error Responses

### 400 Bad Request
```json
{
    "detail": "Missing required GitHub headers"
}
```

### 401 Unauthorized
```json
{
    "detail": "Invalid webhook signature"
}
```

### 500 Internal Server Error
```json
{
    "detail": "Internal server error"
}
```

## Rate Limiting

The API implements rate limiting:
- 100 requests per hour per installation
- Rate limit headers included in responses

## Webhook Events

### Installation Events

1. **created**
   - Triggered when the app is installed
   - Initiates repository scan
   - Creates initial PRs

2. **deleted**
   - Triggered when the app is uninstalled
   - Cleans up resources
   - Removes webhooks

### Pull Request Events

1. **opened**
   - Triggered when a PR is opened
   - Analyzes PR changes
   - Suggests improvements

2. **closed**
   - Triggered when a PR is closed
   - Updates scanning state
   - Triggers new scans if merged

## Configuration

### Environment Variables

Required environment variables:
```env
GITHUB_APP_ID=your_app_id
GITHUB_WEBHOOK_SECRET=your_webhook_secret
PRIVATE_KEY=your_private_key
```

### Repository Configuration

Configure scanning behavior in `.refactorai.yml`:
```yaml
exclude_paths:
  - tests/
  - migrations/

scan_frequency: weekly

refactoring:
  style_improvements: true
  complexity_reduction: true
```

## Examples

### Curl Example

```bash
curl -X POST https://your-domain.com/webhook \
  -H "X-GitHub-Event: installation" \
  -H "X-GitHub-Delivery: 123e4567-e89b-12d3-a456-426614174000" \
  -H "X-Hub-Signature: sha1=..." \
  -H "Content-Type: application/json" \
  -d '{"action":"created","installation":{"id":12345678}}'
```

### Python Example

```python
import httpx

async def send_webhook():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://your-domain.com/webhook",
            headers={
                "X-GitHub-Event": "installation",
                "X-GitHub-Delivery": "123e4567-e89b-12d3-a456-426614174000",
                "X-Hub-Signature": "sha1=...",
                "Content-Type": "application/json"
            },
            json={
                "action": "created",
                "installation": {
                    "id": 12345678
                }
            }
        )
        return response.json()
```
