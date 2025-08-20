# 🚀 SmartLinks Autopilot - Railway Deployment Guide

## Quick Deploy to Railway

### 1. **Connect GitHub Repository**
```bash
# Connect your Railway account to GitHub
# Go to: https://railway.app/new
# Select: "Deploy from GitHub repo"
# Repository: https://github.com/zefparis/smartlinks.git
```

### 2. **Add PostgreSQL Database**
```bash
# In Railway dashboard:
# 1. Click "New" → "Database" → "Add PostgreSQL"
# 2. Note the connection details provided
# 3. Railway will auto-generate DATABASE_URL
```

### 3. **Configure Environment Variables**
Copy these variables to Railway dashboard (Variables tab):

#### **Core Configuration**
```env
PORT=8000
HOST=0.0.0.0
DEBUG=false
ENVIRONMENT=production
FRONTEND_URL=https://your-frontend-domain.vercel.app
```

#### **Database** (Auto-configured by Railway PostgreSQL plugin)
```env
DATABASE_URL=postgresql://user:pass@host:port/db
```

#### **Security & Authentication**
```env
JWT_SECRET_KEY=generate-secure-32-char-key
SESSION_DURATION_HOURS=24
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30
```

#### **Stripe Payment Processing**
```env
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

#### **PayPal Payment Processing**
```env
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_client_secret
PAYPAL_MODE=live
```

#### **Payout Configuration**
```env
MIN_PAYOUT_AMOUNT=10.00
MAX_PAYOUT_AMOUNT=10000.00
PAYOUT_TEST_MODE=false
PAYOUT_AUTO_EXECUTE=true
```

#### **Company Information**
```env
COMPANY_NAME=SmartLinks
COMPANY_ADDRESS=123 Business Street, City, Country
COMPANY_SIRET=12345678901234
COMPANY_VAT=FR12345678901
COMPANY_EMAIL=contact@smartlinks.com
COMPANY_PHONE=+33123456789
COMPANY_WEBSITE=https://smartlinks.com
```

#### **Email Configuration**
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@smartlinks.com
```

#### **Admin Notifications**
```env
ADMIN_ALERT_EMAILS=admin@smartlinks.com
ADMIN_ALERT_SMS=+33123456789
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
ADMIN_REPORT_EMAILS=reports@smartlinks.com
```

#### **Storage & AI**
```env
INVOICE_STORAGE_PATH=/app/storage/invoices
REPORTS_STORAGE_PATH=/app/storage/reports
OPENAI_API_KEY=sk-your-openai-api-key
```

### 4. **Deploy Configuration Files**

The following files are configured for Railway:

- **`railway.json`** - Railway build/deploy configuration
- **`Procfile`** - Process definition
- **`nixpacks.toml`** - Build environment setup
- **`requirements-production.txt`** - Production dependencies

### 5. **Database Migration**
After deployment, run database migrations:

```bash
# Railway will auto-run migrations on deploy
# Or manually via Railway CLI:
railway run python -m alembic upgrade head
```

### 6. **Test Deployment**

#### **Health Check**
```bash
curl https://your-app.railway.app/health
# Expected: {"status": "healthy", "service": "smartlinks-api"}
```

#### **API Documentation**
```bash
# Visit: https://your-app.railway.app/docs
# Should show FastAPI Swagger documentation
```

#### **Test Endpoints**
```bash
# Analytics
curl https://your-app.railway.app/api/analytics/health

# Settings
curl https://your-app.railway.app/api/settings

# Root
curl https://your-app.railway.app/
```

### 7. **Frontend CORS Configuration**

Update your frontend environment variables:
```env
NEXT_PUBLIC_API_URL=https://your-app.railway.app
REACT_APP_API_URL=https://your-app.railway.app
```

### 8. **Production Checklist**

#### **Security**
- [ ] JWT_SECRET_KEY is secure and unique
- [ ] Database credentials are secure
- [ ] CORS origins are properly configured
- [ ] Rate limiting is enabled
- [ ] HTTPS is enforced

#### **Payments**
- [ ] Stripe live keys are configured
- [ ] PayPal live credentials are set
- [ ] Webhook endpoints are configured
- [ ] Payout limits are appropriate

#### **Monitoring**
- [ ] Admin alert emails are configured
- [ ] Slack notifications are working
- [ ] Error tracking is enabled
- [ ] Health checks are responding

#### **Performance**
- [ ] Database connection pooling is configured
- [ ] Redis caching is enabled (optional)
- [ ] File storage is properly configured
- [ ] Background tasks are working

## 🔧 Troubleshooting

### **Common Issues**

#### **Build Failures**
```bash
# Check Railway logs
railway logs

# Common fixes:
# 1. Ensure requirements-production.txt exists
# 2. Check Python version compatibility
# 3. Verify all imports are available
```

#### **Database Connection**
```bash
# Test database connection
railway run python -c "from src.soft.database import engine; print('DB OK')"

# Check environment variables
railway variables
```

#### **CORS Issues**
```bash
# Verify FRONTEND_URL is set correctly
# Check browser console for CORS errors
# Ensure wildcard domains are properly configured
```

#### **Payment Integration**
```bash
# Test Stripe connection
railway run python -c "import stripe; stripe.api_key='sk_test_...'; print(stripe.Account.retrieve())"

# Test PayPal connection
railway run python -c "import paypalrestsdk; print('PayPal SDK loaded')"
```

### **Monitoring & Logs**
```bash
# View real-time logs
railway logs --follow

# Check specific service logs
railway logs --service backend

# Monitor database
railway logs --service postgresql
```

## 🎯 Post-Deployment Tasks

1. **Configure Webhooks**
   - Stripe webhook: `https://your-app.railway.app/api/webhooks/stripe`
   - PayPal webhook: `https://your-app.railway.app/api/webhooks/paypal`

2. **Test Payment Flow**
   - Create test payment
   - Verify payout processing
   - Check invoice generation

3. **Setup Monitoring**
   - Configure Sentry for error tracking
   - Setup uptime monitoring
   - Configure backup schedules

4. **Load Testing**
   - Test API endpoints under load
   - Verify database performance
   - Check rate limiting

## 🚀 Your SmartLinks Cash Machine is Ready!

Backend deployed on Railway with:
- ✅ FastAPI with all cash machine features
- ✅ PostgreSQL database
- ✅ Stripe & PayPal integration
- ✅ Automated payouts & invoicing
- ✅ Security & rate limiting
- ✅ Monitoring & alerts
- ✅ CORS configured for frontend

**API Base URL**: `https://your-app.railway.app`
**Documentation**: `https://your-app.railway.app/docs`
