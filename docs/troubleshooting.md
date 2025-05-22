# Troubleshooting Guide

## Common Issues and Solutions

### GitHub App Issues

#### 1. Webhook Delivery Failures

**Symptoms**:
- No webhook events received
- 401 Unauthorized errors
- Missing webhook deliveries

**Solutions**:
1. Check webhook configuration:
   ```bash
   # Verify webhook URL
   curl -X POST https://your-domain.com/webhook \
     -H "X-GitHub-Event: ping" \
     -H "X-Hub-Signature: sha1=..." \
     -d '{"zen":"Design for failure."}'
   ```

2. Verify webhook secret:
   ```env
   # .env
   GITHUB_WEBHOOK_SECRET=your_webhook_secret
   ```

3. Check SSL certificate:
   ```bash
   # Test SSL
   openssl s_client -connect your-domain.com:443
   ```

#### 2. Authentication Failures

**Symptoms**:
- 401 Unauthorized errors
- JWT token issues
- Installation access token problems

**Solutions**:
1. Verify GitHub App credentials:
   ```env
   # .env
   GITHUB_APP_ID=your_app_id
   PRIVATE_KEY=your_private_key
   ```

2. Regenerate private key:
   - Go to GitHub App settings
   - Generate new private key
   - Update environment variables

3. Check installation ID:
   ```env
   # .env
   GITHUB_INSTALLATION_ID=your_installation_id
   ```

### OpenAI Integration Issues

#### 1. API Rate Limits

**Symptoms**:
- 429 Too Many Requests errors
- Slow response times
- Incomplete refactoring

**Solutions**:
1. Implement rate limiting:
   ```python
   # Add rate limiting
   from ratelimit import limits, sleep_and_retry

   @sleep_and_retry
   @limits(calls=60, period=60)
   def call_openai_api():
       # Implementation
       pass
   ```

2. Add retry logic:
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential

   @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
   def call_openai_with_retry():
       # Implementation
       pass
   ```

#### 2. Model Response Issues

**Symptoms**:
- Inconsistent refactoring
- Poor code quality
- Missing context

**Solutions**:
1. Improve prompts:
   ```python
   # Example improved prompt
   PROMPT = """
   You are a Python expert. Refactor the following code to improve:
   - Readability
   - Performance
   - Maintainability

   Code:
   {code}

   Context:
   {context}
   """
   ```

2. Add context:
   ```python
   def get_code_context(file_path: str) -> str:
       # Implementation
       pass
   ```

### Code Scanner Issues

#### 1. False Positives

**Symptoms**:
- Incorrect refactoring suggestions
- Unnecessary changes
- Style conflicts

**Solutions**:
1. Adjust thresholds:
   ```yaml
   # .refactorai.yml
   max_complexity: 10
   min_maintainability: 50
   ```

2. Add exclusions:
   ```yaml
   # .refactorai.yml
   exclude_paths:
     - tests/
     - migrations/
     - generated/
   ```

#### 2. Performance Issues

**Symptoms**:
- Slow scanning
- High memory usage
- Timeout errors

**Solutions**:
1. Optimize file processing:
   ```python
   # Process files in chunks
   def process_files_in_chunks(files: List[str], chunk_size: int = 10):
       for i in range(0, len(files), chunk_size):
           chunk = files[i:i + chunk_size]
           # Process chunk
   ```

2. Add caching:
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=100)
   def analyze_file(file_path: str) -> Dict:
       # Implementation
       pass
   ```

### Deployment Issues

#### 1. Server Errors

**Symptoms**:
- 500 Internal Server Error
- Connection timeouts
- Worker crashes

**Solutions**:
1. Check logs:
   ```bash
   # View logs
   tail -f /var/log/ai-refactor-bot.log
   ```

2. Monitor resources:
   ```bash
   # Check memory usage
   ps aux | grep ai-refactor-bot
   ```

#### 2. Scaling Issues

**Symptoms**:
- Slow response times
- Worker overload
- Memory leaks

**Solutions**:
1. Adjust worker count:
   ```bash
   # Update worker count
   gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. Implement caching:
   ```python
   # Add Redis caching
   from redis import Redis
   redis_client = Redis(host='localhost', port=6379, db=0)
   ```

## Debugging Tools

### 1. Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='debug.log'
)
```

### 2. Monitoring

```python
# Add metrics
from prometheus_client import Counter, Histogram

request_count = Counter('http_requests_total', 'Total HTTP requests')
request_latency = Histogram('http_request_duration_seconds', 'HTTP request latency')
```

### 3. Error Tracking

```python
# Add error tracking
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

## Getting Help

1. **Check Logs**
   - Application logs
   - System logs
   - GitHub webhook logs

2. **Community Support**
   - GitHub Issues
   - Stack Overflow
   - Discord community

3. **Professional Support**
   - Contact maintainers
   - Enterprise support
   - Consulting services
