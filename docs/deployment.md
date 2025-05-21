# Deployment Guide

## Overview

This guide covers deploying the AI Refactoring Bot to various platforms. The application is designed to be deployed as a web service that can receive GitHub webhooks.

## Prerequisites

- Python 3.8 or higher
- GitHub App credentials
- OpenAI API key
- A domain name (for webhook URLs)
- SSL certificate (for secure webhook delivery)

## Deployment Options

### 1. Railway Deployment

1. **Create Railway Account**
   - Sign up at [Railway.app](https://railway.app)
   - Install Railway CLI: `npm i -g @railway/cli`

2. **Initialize Project**
   ```bash
   railway init
   ```

3. **Configure Environment**
   ```bash
   railway variables set \
     GITHUB_APP_ID=your_app_id \
     GITHUB_WEBHOOK_SECRET=your_webhook_secret \
     PRIVATE_KEY=your_private_key \
     OPENAI_API_KEY=your_openai_key
   ```

4. **Deploy**
   ```bash
   railway up
   ```

### 2. Docker Deployment

1. **Build Image**
   ```bash
   docker build -t ai-refactor-bot .
   ```

2. **Run Container**
   ```bash
   docker run -d \
     -p 3000:3000 \
     -e GITHUB_APP_ID=your_app_id \
     -e GITHUB_WEBHOOK_SECRET=your_webhook_secret \
     -e PRIVATE_KEY=your_private_key \
     -e OPENAI_API_KEY=your_openai_key \
     ai-refactor-bot
   ```

### 3. Manual Deployment

1. **Server Setup**
   ```bash
   # Install dependencies
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

   # Set up environment variables
   cp .env.example .env
   # Edit .env with your values
   ```

2. **Run with Gunicorn**
   ```bash
   gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:3000
   ```

## Environment Variables

Required variables:
```env
# GitHub App Configuration
GITHUB_APP_ID=your_app_id
GITHUB_WEBHOOK_SECRET=your_webhook_secret
PRIVATE_KEY=your_private_key

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Server Configuration
PORT=3000
HOST=0.0.0.0
```

## GitHub App Setup

1. **Create GitHub App**
   - Go to GitHub Settings > Developer Settings > GitHub Apps
   - Click "New GitHub App"
   - Fill in required fields
   - Set webhook URL to your deployment URL
   - Generate private key

2. **Configure Permissions**
   - Repository permissions:
     - Contents: Read & write
     - Pull requests: Read & write
     - Metadata: Read-only
   - Subscribe to events:
     - Installation
     - Pull request
     - Push

3. **Install App**
   - Install on your repositories
   - Note the installation ID

## Monitoring

### Health Checks

1. **Endpoint**
   ```http
   GET /ping
   ```

2. **Response**
   ```json
   {
       "status": "ok",
       "message": "pong"
   }
   ```

### Logging

- Application logs are available in your deployment platform
- Use `LOG_LEVEL` environment variable to control verbosity

## Scaling

### Horizontal Scaling

1. **Multiple Workers**
   ```bash
   gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. **Load Balancer**
   - Configure your load balancer to distribute traffic
   - Ensure sticky sessions if needed

### Vertical Scaling

1. **Resource Allocation**
   - Adjust worker count based on CPU cores
   - Monitor memory usage
   - Scale based on metrics

## Backup and Recovery

1. **Configuration Backup**
   - Backup `.env` files
   - Backup GitHub App credentials
   - Backup SSL certificates

2. **Recovery Procedure**
   - Restore environment variables
   - Verify GitHub App configuration
   - Test webhook delivery

## Troubleshooting

Common issues and solutions:

1. **Webhook Delivery Failures**
   - Check SSL certificate
   - Verify webhook secret
   - Check server logs

2. **Rate Limiting**
   - Monitor GitHub API limits
   - Implement caching
   - Use rate limit headers

3. **Performance Issues**
   - Check worker count
   - Monitor memory usage
   - Review logging levels
