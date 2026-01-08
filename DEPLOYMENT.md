# Heroku Deployment Guide - UniOr-PET

This guide explains how to deploy both the **Translator Interface** and **Project Manager Dashboard** on Heroku from the same codebase.

## Architecture

The codebase now includes a `launcher.py` script that determines which app to run based on the `APP_MODE` environment variable. This allows you to deploy:

1. **Translator App** - Main post-editing interface for translators
2. **Manager App** - Analytics and management dashboard for project managers

Both apps can be deployed from the same GitHub repository to separate Heroku apps.

---

## Option 1: Two Separate Heroku Apps (Recommended)

Deploy two Heroku apps from the same codebase:

### Step 1: Create Two Heroku Apps

```bash
# Create translator app
heroku create unior-pet-translator

# Create manager app
heroku create unior-pet-manager
```

### Step 2: Configure Environment Variables

**For Translator App:**
```bash
heroku config:set APP_MODE=translator -a unior-pet-translator

# Add your secrets
heroku config:set PROJECT_URL="your_supabase_url" -a unior-pet-translator
heroku config:set PROJECT_API_KEY="your_supabase_key" -a unior-pet-translator
heroku config:set MONGO_CONNECTION_STRING="your_mongo_url" -a unior-pet-translator
```

**For Manager App:**
```bash
heroku config:set APP_MODE=manager -a unior-pet-manager

# Add your secrets (same as translator)
heroku config:set PROJECT_URL="your_supabase_url" -a unior-pet-manager
heroku config:set PROJECT_API_KEY="your_supabase_key" -a unior-pet-manager
heroku config:set MONGO_CONNECTION_STRING="your_mongo_url" -a unior-pet-manager
```

### Step 3: Deploy Both Apps

**Deploy Translator App:**
```bash
git push heroku main
```

**Deploy Manager App:**
```bash
# Add manager remote
git remote add heroku-manager https://git.heroku.com/unior-pet-manager.git

# Push to manager app
git push heroku-manager main
```

### Step 4: Access Your Apps

- **Translator Interface**: `https://unior-pet-translator.herokuapp.com`
- **Manager Dashboard**: `https://unior-pet-manager.herokuapp.com`

---

## Option 2: Single Heroku App with Manual Switching

If you prefer to use a single Heroku app and manually switch between modes:

### Deploy Single App

```bash
heroku create unior-pet

# Set to translator mode (default)
heroku config:set APP_MODE=translator -a unior-pet

# Deploy
git push heroku main
```

### Switch Modes

**Switch to Manager mode:**
```bash
heroku config:set APP_MODE=manager -a unior-pet
heroku restart -a unior-pet
```

**Switch back to Translator mode:**
```bash
heroku config:set APP_MODE=translator -a unior-pet
heroku restart -a unior-pet
```

**Note**: This approach requires manual intervention to switch between interfaces, so Option 1 is recommended.

---

## Files Modified for Deployment

1. **launcher.py** - New launcher script that routes to appropriate app
2. **Procfile** - Updated to use launcher: `web: sh setup.sh && python launcher.py`
3. **requirements.txt** - Added management dependencies (plotly, openpyxl)

---

## Environment Variables Required

Both apps need the following environment variables:

```bash
APP_MODE=translator  # or "manager"
PROJECT_URL=your_supabase_url
PROJECT_API_KEY=your_supabase_api_key
MONGO_CONNECTION_STRING=your_mongo_connection_string
VERSION=1.0.0
```

You can also set these in `.streamlit/secrets.toml` for local development.

---

## Troubleshooting

### App won't start
- Check Heroku logs: `heroku logs --tail -a your-app-name`
- Verify APP_MODE is set correctly: `heroku config -a your-app-name`

### Wrong interface appears
- Verify APP_MODE environment variable
- Restart app: `heroku restart -a your-app-name`

### Database connection errors
- Ensure all environment variables are set
- Check that Supabase/MongoDB credentials are correct
- Verify IP whitelist for MongoDB (should allow all IPs for Heroku: 0.0.0.0/0)

---

## Local Testing

Test the launcher locally:

**Translator mode:**
```bash
export APP_MODE=translator
python launcher.py
```

**Manager mode:**
```bash
export APP_MODE=manager
python launcher.py
```

Or run directly:
```bash
streamlit run app.py  # Translator
streamlit run management/0_🏢_Manager.py  # Manager
```

---

## Cost Considerations

- **Free Tier**: You can run both apps on Heroku's free tier (550-1000 dyno hours/month)
- **Hobby Tier** ($7/month per app): Recommended for production use
  - No dyno sleeping
  - SSL certificates
  - Better performance

---

## Recommended Workflow

1. **Development**: Run both apps locally on different ports
   ```bash
   streamlit run app.py --server.port 8501  # Translator
   streamlit run management/0_🏢_Manager.py --server.port 8502  # Manager
   ```

2. **Staging**: Deploy to two separate Heroku apps with free tier

3. **Production**: Upgrade both apps to Hobby tier for better reliability

---

## Need Help?

- Check Heroku logs: `heroku logs --tail -a your-app-name`
- Verify environment variables: `heroku config -a your-app-name`
- Restart app: `heroku restart -a your-app-name`
