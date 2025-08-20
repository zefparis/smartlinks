#!/bin/bash

# SmartLinks Autopilot - Railway Deployment Script
# Run this script to deploy to Railway

echo "🚀 Deploying SmartLinks Autopilot to Railway..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Login to Railway (if not already logged in)
echo "🔐 Checking Railway authentication..."
railway login

# Create new project or link existing
echo "📦 Setting up Railway project..."
railway link

# Add PostgreSQL database
echo "🗄️ Adding PostgreSQL database..."
railway add --database postgresql

# Set environment variables
echo "⚙️ Setting environment variables..."

# Core configuration
railway variables set PORT=8000
railway variables set HOST=0.0.0.0
railway variables set DEBUG=false
railway variables set ENVIRONMENT=production

# Security
railway variables set JWT_SECRET_KEY=$(openssl rand -base64 32)
railway variables set SESSION_DURATION_HOURS=24
railway variables set MAX_LOGIN_ATTEMPTS=5
railway variables set LOCKOUT_DURATION_MINUTES=30

# Payout configuration
railway variables set MIN_PAYOUT_AMOUNT=10.00
railway variables set MAX_PAYOUT_AMOUNT=10000.00
railway variables set PAYOUT_TEST_MODE=false
railway variables set PAYOUT_AUTO_EXECUTE=true

# Company info (update these)
railway variables set COMPANY_NAME="SmartLinks"
railway variables set COMPANY_EMAIL="contact@ia-solution.fr"
railway variables set COMPANY_PHONE="+33123456789"
railway variables set COMPANY_WEBSITE="https://smartlinks.com"

# Storage paths
railway variables set INVOICE_STORAGE_PATH="/app/storage/invoices"
railway variables set REPORTS_STORAGE_PATH="/app/storage/reports"

echo "⚠️  IMPORTANT: Set these variables manually in Railway dashboard:"
echo "   - STRIPE_SECRET_KEY=sk_live_..."
echo "   - STRIPE_PUBLISHABLE_KEY=pk_live_..."
echo "   - PAYPAL_CLIENT_ID=..."
echo "   - PAYPAL_CLIENT_SECRET=..."
echo "   - SMTP_USER=your-email@gmail.com"
echo "   - SMTP_PASSWORD=your-app-password"
echo "   - FRONTEND_URL=https://your-frontend-domain.vercel.app"

# Deploy
echo "🚀 Deploying to Railway..."
railway up

echo "✅ Deployment complete!"
echo "📋 Next steps:"
echo "   1. Set remaining environment variables in Railway dashboard"
echo "   2. Configure Stripe/PayPal webhooks"
echo "   3. Test API endpoints"
echo "   4. Update frontend API URL"

# Get the deployment URL
echo "🌐 Your API will be available at:"
railway status
