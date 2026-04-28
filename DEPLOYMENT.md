# PUP MOA Tracking System - PostgreSQL/Neon Migration Guide

## Overview
This guide documents the migration from SQLite (`moa.db`) to PostgreSQL (Neon.tech) on Render.com.

## Project Structure
```
app/
├── __init__.py          # Flask app factory with database initialization
├── models.py            # Database models (User, Student, StudentRecord)
├── routes.py            # Application routes
├── templates/           # HTML templates
└── static/              # CSS/JavaScript

config.py               # Configuration with DATABASE_URL handling
create_director.py      # Script to initialize Director admin account
requirements.txt        # Python dependencies
runtime.txt             # Python version specification
Dockerfile              # Docker container configuration
render.yaml             # Render.com deployment configuration
```

## Database Configuration

### Environment Variables Required
Set these on Render.com in the Environment section:

```bash
DATABASE_URL=postgresql://username:password@host/database?sslmode=require
SECRET_KEY=your-secure-random-key
ADMIN_USER=admin
ADMIN_PASSWORD=secure-password
DIRECTOR_USERNAME=director
DIRECTOR_PASSWORD=ChangeMe@2024
```

### How it Works
1. **config.py** reads `DATABASE_URL` from environment
2. Automatically converts `postgres://` → `postgresql://` (SQLAlchemy 2.0+ requirement)
3. Falls back to `sqlite:///moa.db` if `DATABASE_URL` not set (local development)

### Local Development (.env file)
```bash
# .env (Git-ignored)
DATABASE_URL=sqlite:///moa.db
SECRET_KEY=dev-key-change-in-production
ADMIN_USER=admin
ADMIN_PASSWORD=admin123
```

## Deployment Steps

### 1. Initial Database Setup

Connect to your Render PostgreSQL (Neon) and verify it's accessible:

```bash
# Test connection (optional)
psql $DATABASE_URL
```

### 2. Deploy to Render

Push to the `whigan` branch:

```bash
git push origin whigan
```

Render will automatically:
- Install dependencies from `requirements.txt`
- Run the app with `gunicorn` (specified in `Procfile`)
- Create database tables via `db.create_all()` in `app/__init__.py`

### 3. Initialize Director Account

After first deployment, SSH into Render and run:

```bash
python create_director.py
```

Or run locally with production DATABASE_URL:

```bash
export DATABASE_URL="postgresql://..."
python create_director.py
```

### 4. Verify Deployment

```bash
curl https://<your-render-app>.onrender.com
```

Should display the login choice page.

## Key Features of This Setup

### ✅ Automatic Table Creation
- `db.create_all()` runs inside `app.app_context()` block
- Works with both SQLite and PostgreSQL
- Runs only on app startup
- Includes error handling and logging

### ✅ PostgreSQL Compatibility
- `psycopg2-binary` driver included in requirements
- Handles `postgres://` → `postgresql://` protocol conversion
- Database connection pooling through SQLAlchemy 2.0

### ✅ Admin Account Management
- `create_director.py` script for initialization
- Secure password hashing with Werkzeug
- Role-based access control (admin/student)

### ✅ SQLite Fallback
- Works offline in development without Postgres
- Automatic schema migration for new columns
- Useful for testing before production

## Troubleshooting

### Database Connection Error
**Problem**: `OperationalError: could not connect to server`

**Solution**:
1. Verify `DATABASE_URL` is set on Render
2. Check Neon credentials are correct
3. Ensure SSL mode is set (usually `?sslmode=require`)
4. Test locally with: `export DATABASE_URL="..."; python -c "from app import create_app; app = create_app()"`

### Tables Not Created
**Problem**: `ProgrammingError: relation "users" does not exist`

**Solution**:
1. Check that deployment completed successfully
2. SSH into Render and manually run: `python create_director.py`
3. Verify `db.create_all()` executed (check logs)

### Director Account Already Exists
**Problem**: Running `create_director.py` again shows account exists

**Solution**: 
- This is expected behavior
- If you need to reset, delete via SQL: `DELETE FROM users WHERE username='director';`

## Production Checklist

- [ ] Neon PostgreSQL database created
- [ ] DATABASE_URL set on Render environment
- [ ] SECRET_KEY set to secure random value
- [ ] Deployed to `whigan` branch
- [ ] `create_director.py` executed
- [ ] Director can log in: director/ChangeMe@2024
- [ ] Changed initial Director password
- [ ] Student registration working
- [ ] Admin dashboard accessible
- [ ] File uploads working (check `uploads/` folder permissions)

## Security Notes

1. **Change default passwords immediately** after first login
2. **Set strong SECRET_KEY** for session encryption
3. **Use SSL/TLS** (Render automatically provides this)
4. **Neon credentials** are kept in environment, never in code
5. **Database backups** are handled by Neon/Render

## Useful Commands

### Local Testing
```bash
# Activate virtual environment
source .venv/Scripts/activate  # Windows PowerShell
# or
.venv\Scripts\Activate.ps1     # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Run local development server
python run.py
```

### View Render Logs
```bash
# In Render dashboard or via CLI
render logs <service-id>
```

### Create Additional Admin Users
```python
from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    new_admin = User(username="admin2", role="admin")
    new_admin.set_password("secure_password")
    db.session.add(new_admin)
    db.session.commit()
    print(f"Created admin: admin2")
```

## References

- [Neon PostgreSQL Documentation](https://neon.tech/docs)
- [Render Deployment Guide](https://render.com/docs)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Flask-SQLAlchemy Guide](https://flask-sqlalchemy.palletsprojects.com/)
