# Heroku Deployment Guide for UniOr-PET

This guide will help you deploy your UniOr-PET application on Heroku.

## Prerequisites

1. **Heroku Account**: Create a free account at [heroku.com](https://www.heroku.com/)
2. **Heroku CLI**: Install from [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
3. **Git**: Make sure git is installed on your system

## Files Required (Already Created)

✅ `Procfile` - Tells Heroku how to run the app
✅ `setup.sh` - Configures Streamlit settings
✅ `runtime.txt` - Specifies Python 3.10.6
✅ `requirements.txt` - Lists all Python dependencies
✅ `.gitignore` - Prevents sensitive files from being committed

## Step-by-Step Deployment

### 1. Install Heroku CLI

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Ubuntu/Debian
curl https://cli-assets.heroku.com/install.sh | sh

# Windows
# Download installer from https://devcenter.heroku.com/articles/heroku-cli
```

### 2. Login to Heroku

```bash
heroku login
```

This will open a browser window for you to login.

### 3. Initialize Git Repository (if not already done)

```bash
# Check if git is initialized
git status

# If not initialized, run:
git init
git add .
git commit -m "Initial commit for Heroku deployment"
```

### 4. Create Heroku App

```bash
# Create a new Heroku app
heroku create unior-pet-app

# Or let Heroku generate a random name
heroku create
```

This will create an app and add a git remote called `heroku`.

### 5. Set Environment Variables

You need to configure your environment variables (from `.env` file) on Heroku:

```bash
# Supabase configuration
heroku config:set PROJECT_URL="https://xlsmdqmkdknjkhteajqu.supabase.co"
heroku config:set PROJECT_API_KEY="sb_publishable_TlrZMgaiXF33LUB_VIdqTA_RzoHRkcu"

# App version
heroku config:set VERSION="1.0.0"

# Optional: MongoDB (if you want to keep it as fallback)
heroku config:set MONGO_CONNECTION_STRING="your-mongodb-connection-string"
```

**Security Note**: Never commit `.env` or secrets to git. Always use `heroku config:set` for sensitive data.

### 6. Deploy to Heroku

```bash
# Push your code to Heroku
git push heroku main

# If your branch is named 'master', use:
# git push heroku master
```

This will:
- Upload your code to Heroku
- Install Python dependencies from `requirements.txt`
- Run the setup script
- Start your Streamlit app

### 7. Open Your App

```bash
# Open the app in your browser
heroku open
```

### 8. View Logs (if needed)

```bash
# View real-time logs
heroku logs --tail

# View recent logs
heroku logs --tail -n 100
```

## Troubleshooting

### Common Issues

**1. Build Fails - Large Dependencies**

Some ML dependencies (like `unbabel-comet`, `bert-score`) are very large. Heroku has a slug size limit of 500MB.

**Solution**: Consider using the lighter version or removing unused dependencies:

```bash
# Check slug size
heroku plugins:install heroku-repo
heroku repo:purge_cache -a unior-pet-app
```

If you need to reduce dependencies, edit `requirements.txt` and redeploy.

**2. App Crashes on Startup**

Check logs:
```bash
heroku logs --tail
```

Common causes:
- Missing environment variables
- Incorrect `Procfile` configuration
- Port binding issues (Streamlit should use `$PORT`)

**3. Database Connection Issues**

Verify environment variables are set:
```bash
heroku config
```

Test connection from Heroku dyno:
```bash
heroku run python -c "from db_manager import get_default_supabase_manager; print(get_default_supabase_manager())"
```

**4. Out of Memory Errors**

Heroku free tier has 512MB RAM. If your app uses more:

**Solution**: Upgrade to a paid dyno:
```bash
# Upgrade to Hobby dyno ($7/month, 1GB RAM)
heroku ps:scale web=1:hobby
```

## Updating Your App

After making changes:

```bash
# Commit changes
git add .
git commit -m "Description of changes"

# Deploy to Heroku
git push heroku main
```

## Monitoring

### Check App Status
```bash
heroku ps
```

### View Metrics
```bash
# Open metrics dashboard
heroku addons:create librato:development
```

### Restart App
```bash
heroku restart
```

## Scaling

### Scale Dynos
```bash
# Scale up (more instances)
heroku ps:scale web=2

# Scale down
heroku ps:scale web=1
```

## Cost Considerations

### Free Tier Limitations:
- **550-1000 dyno hours/month** (sleeps after 30 min of inactivity)
- **512MB RAM**
- **Slug size limit: 500MB**

### Recommended Upgrades:
- **Hobby Dyno** ($7/month): No sleep, 1GB RAM
- **Standard Dyno** ($25/month): Better performance, 2.5GB RAM

## Environment-Specific Settings

### Production vs Development

You can create multiple environments:

```bash
# Create staging environment
heroku create unior-pet-staging --remote staging

# Deploy to staging
git push staging main

# Deploy to production
git push heroku main
```

## Security Best Practices

1. **Never commit secrets** to git
2. **Use `heroku config:set`** for all sensitive data
3. **Enable SSL** (automatic on Heroku)
4. **Use Row Level Security** in Supabase
5. **Regularly update dependencies**:
   ```bash
   pip list --outdated
   ```

## Backup Strategy

### Database Backups

Since you're using Supabase, backups are automatic. But you should:

1. **Regularly export data**:
   - Go to Supabase Dashboard
   - Database > Backups
   - Download backups

2. **Test restore procedures** periodically

## Domain Setup (Optional)

### Use Custom Domain

```bash
# Add custom domain
heroku domains:add www.yourapp.com

# Follow DNS configuration instructions
heroku domains
```

Then update your DNS provider with the CNAME record shown.

## Monitoring and Alerts

### Set up logging
```bash
# Add Papertrail for log management
heroku addons:create papertrail:choklad
```

### Monitor errors
```bash
# Add Sentry for error tracking
heroku addons:create sentry:f1
```

## Getting Help

- **Heroku Status**: [status.heroku.com](https://status.heroku.com/)
- **Heroku Support**: [help.heroku.com](https://help.heroku.com/)
- **App Issues**: Check logs with `heroku logs --tail`

## Quick Reference Commands

```bash
# Deploy
git push heroku main

# View logs
heroku logs --tail

# Restart app
heroku restart

# Open app
heroku open

# Check status
heroku ps

# Set config
heroku config:set KEY=value

# View config
heroku config

# Run command
heroku run python script.py

# SSH into dyno
heroku run bash
```

## Next Steps

After deployment:

1. ✅ Test all features on Heroku
2. ✅ Set up monitoring
3. ✅ Configure custom domain (optional)
4. ✅ Share the URL with your users!

---

Need help? Contact [antonio.castaldo@phd.unipi.it](mailto:antonio.castaldo@phd.unipi.it)
