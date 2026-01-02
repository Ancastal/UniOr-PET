# Database Setup Guide

UniOr-PET supports multiple database options with different workflows for Project Managers and Translators.

## User Roles

### Project Managers
Project Managers create projects and choose where to store their project data. They receive a **project key** that they share with their translators.

### Translators
Translators join existing projects using a **project key** provided by their Project Manager. They automatically use the same database as their Project Manager.

---

## For Project Managers: Database Options

### 1. Free Supabase (Recommended)
Use the shared Supabase database provided by UniOr-PET. This is the easiest option and requires no setup on your part.

**Pros:**
- No setup required
- Free tier includes 500MB storage
- Automatic backups
- Fast and reliable

**Cons:**
- Shared database (your data is isolated but stored with other projects)
- Data stored on our server

**How to use:**
1. During registration, select "Project Manager"
2. Choose "Free Supabase (Recommended)" as your database option
3. Complete registration
4. You'll receive a project key like: **Surname_Name**
5. Share this key with your translators

---

### 2. Your Own MongoDB Database
Use your own MongoDB database for complete control over your project data.

**Pros:**
- Full control over your data
- Can use MongoDB Atlas free tier (512MB)
- Private and isolated

**Cons:**
- Requires setup
- Need to manage your own database

**Setup Instructions:**

1. **Create a MongoDB Atlas Account**
   - Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - Sign up for a free account

2. **Create a Cluster**
   - Choose the free tier (M0)
   - Select your preferred region
   - Create the cluster

3. **Set Up Database Access**
   - Go to "Database Access" in the sidebar
   - Add a new database user with a username and password
   - Save these credentials

4. **Set Up Network Access**
   - Go to "Network Access" in the sidebar
   - Click "Add IP Address"
   - Select "Allow Access from Anywhere" (0.0.0.0/0)
   - Confirm

5. **Get Connection String**
   - Go back to your cluster
   - Click "Connect"
   - Select "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your database user password
   - Replace `<dbname>` with your database name (e.g., `mtpe_database`)

6. **Use in UniOr-PET**
   - During registration, select "Project Manager"
   - Choose "My Own MongoDB"
   - Paste your connection string
   - Example: `mongodb+srv://username:password@cluster.domain.mongodb.net/mtpe_database`
   - Complete registration and save your project key
   - Share the project key with your translators

---

### 3. Your Own Supabase Database
Use your own Supabase project for maximum flexibility.

**Pros:**
- Full control over your data
- Supabase free tier includes 500MB
- Built-in authentication and real-time features
- Private and isolated

**Cons:**
- Requires setup
- Need to manage your own project

**Setup Instructions:**

1. **Create a Supabase Account**
   - Go to [Supabase](https://supabase.com)
   - Sign up for a free account

2. **Create a New Project**
   - Click "New Project"
   - Choose a name and password
   - Select your region
   - Wait for project setup to complete

3. **Set Up Database Tables**
   - Go to the SQL Editor in your Supabase dashboard
   - Copy the contents of `supabase_setup.sql` from this repository
   - Paste and run the SQL script
   - This will create the necessary tables

4. **Get Your Credentials**
   - Go to Settings > API
   - Copy your "Project URL"
   - Copy your "anon/public" API key

5. **Use in UniOr-PET**
   - During registration, select "Project Manager"
   - Choose "My Own Supabase"
   - Enter your Project URL (e.g., `https://yourproject.supabase.co`)
   - Enter your API key
   - Complete registration and save your project key
   - Share the project key with your translators

---

## For Translators: Joining a Project

**How to Join:**

1. **Get Your Project Key**
   - Ask your Project Manager for the project key
   - Format: `Surname_Name` (e.g., `Smith_John`)

2. **Register**
   - Go to the UniOr-PET registration page
   - Select "Translator" as your role
   - Enter your name, surname, and password
   - Enter the project key provided by your Project Manager
   - Complete registration

3. **Start Working**
   - Login with your credentials
   - Your data will automatically be stored in the same database as your Project Manager
   - No additional setup required!

**Important Notes:**
- You don't need to choose a database option - you automatically use your PM's database
- Make sure you enter the correct project key
- Contact your Project Manager if you don't have a project key

---

## For Developers: Setting Up the Default Free Database

If you're deploying your own instance of UniOr-PET, you'll need to set up the default Supabase database:

1. Create a Supabase project (follow steps 1-3 from "Your Own Supabase" above)

2. Run the `supabase_setup.sql` script in your SQL Editor

3. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` with your Supabase credentials:
   ```
   PROJECT_URL=https://your-project.supabase.co
   PROJECT_API_KEY=your-supabase-anon-key
   DATABASE_NAME=UniOr-PET
   ```

5. For Streamlit Cloud deployment, add these to your secrets.toml:
   ```toml
   PROJECT_URL = "https://your-project.supabase.co"
   PROJECT_API_KEY = "your-supabase-anon-key"
   ```

---

## Troubleshooting

### Connection Issues

**MongoDB Connection Fails:**
- Check that your IP is whitelisted (or use 0.0.0.0/0 for all IPs)
- Verify your username and password are correct
- Make sure you replaced `<password>` and `<dbname>` in the connection string
- Check that your cluster is running

**Supabase Connection Fails:**
- Verify your Project URL is correct
- Check that your API key is the "anon/public" key
- Make sure you ran the SQL setup script
- Check that your project is active

### Data Not Saving

- Verify you selected the correct database type during registration
- Check that your connection string/credentials are valid
- Look for error messages in the app

---

## Security Notes

- **Never share your database credentials publicly**
- For MongoDB, use IP whitelisting when possible
- For Supabase, you can enable Row Level Security (RLS) for additional protection
- Change default passwords and use strong passwords
- Regularly backup your data

---

## Need Help?

If you encounter any issues, please:
1. Check this guide thoroughly
2. Review error messages carefully
3. Contact [antonio.castaldo@phd.unipi.it](mailto:antonio.castaldo@phd.unipi.it)
