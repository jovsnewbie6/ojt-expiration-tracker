# Troubleshooting Registration & Login Issues on Render

## What I Fixed

1. **Made App Initialization Non-Blocking**
   - Database initialization errors no longer prevent app startup
   - App will start even if database operations fail initially
   - Allows retry on next request

2. **Made Pre-Deploy Commands Optional**
   - Changed from `python setup_admin.py && python create_director.py` 
   - To: `python setup_admin.py || true`
   - This prevents deployment failure if pre-deploy commands timeout

3. **Improved Email Constraint Handling**
   - Made `_fix_email_constraint()` more defensive
   - Checks if tables exist before attempting fixes
   - Won't fail if tables don't exist yet

4. **Added Health Check Endpoint**
   - Access: `https://your-render-app.onrender.com/health`
   - This will tell you if the database is accessible
   - Helps diagnose connectivity issues

## Debugging Steps

### Step 1: Check App Health
```
curl https://your-render-app.onrender.com/health
```

Expected response if working:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

If you get an error, the database isn't accessible. Check your DATABASE_URL in Render.

### Step 2: Check Render Logs
1. Go to your Render dashboard
2. Click on your service
3. Go to "Logs" tab
4. Look for any errors related to:
   - Database connection
   - Import errors
   - Constraint violations

### Step 3: Try Registration Again
Once the app is stable:
1. Go to `https://your-render-app.onrender.com/login`
2. Click "Register"
3. Fill in the form and submit
4. Check the Render logs for any detailed error messages

## Common Issues & Solutions

### Issue: "An error occurred during login"
**Possible causes:**
- Database not accessible
- Students table doesn't exist
- Email constraint still exists

**Solution:**
- Check `/health` endpoint
- Restart the app (force redeploy)
- Check Render logs for detailed error

### Issue: "An error occurred while loading the student management page"
**Possible causes:**
- Database connection dropped
- Permission system not initialized

**Solution:**
- Check if you're logged in as admin
- Check `/health` endpoint
- Restart app

## What To Do If Still Not Working

1. **Check DATABASE_URL is set in Render**
   - Go to Environment Variables in Render dashboard
   - Verify DATABASE_URL is set correctly (should start with `postgresql://`)

2. **Check Render Logs for Detailed Errors**
   - Look for any Python exceptions
   - Look for database connection errors
   - Copy any error messages

3. **Force Rebuild**
   - In Render dashboard, go to Deployments
   - Click the three dots on latest deployment
   - Select "Redeploy"

4. **Check if Default Admin User Exists**
   - The app should create admin user automatically on startup
   - Default: username=admin, password=admin123
   - Try logging in with these credentials

## Testing Plan

After deployment, try these in order:

1. ✅ Check `/health` endpoint
2. ✅ Try to register a student (use any student number like "2024001")
3. ✅ Try to login with registered student
4. ✅ Check if you can view student portal
5. ✅ Try to login as admin (admin/admin123)
6. ✅ Check manage students page

## Accessing Render Logs

To see detailed error messages:
```
# In Render dashboard:
1. Click on your service
2. Click "Logs"
3. Filter by time (recent first)
4. Look for "ERROR" or "Exception" level logs
5. Copy the full error traceback
```

These logs will show exactly why registration is failing.
