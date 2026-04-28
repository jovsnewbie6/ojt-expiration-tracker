# PUP MOA Tracking System

A professional system for tracking OJT (On-the-Job Training) MOA (Memorandum of Agreement) expiration dates, student records, and admin management. Built with Flask and PostgreSQL for Poly University of the Philippines (PUP).

## 🎯 Features

### Student Portal
- Student registration and authentication
- MOA record submission with expiration dates
- Document attachment management (PDFs)
- Real-time progress tracking on requirements
- Password change and account management
- Status notifications (Pending, Incomplete, Approved)

### Admin Dashboard
- Review and manage all student submissions
- Update MOA status and expiration information
- Track document completeness (Resume, Medical Certificate, MOA, Insurance, etc.)
- Export approved records to Excel
- Search and filter submissions
- Download CSV reports

### Account Management
- **Soft Delete (Deactivation)**: Deactivate user accounts without deleting data
- **Admin Staff Management**: Create and manage admin accounts
- **Student Account Management**: View all students and toggle account status
- **Security**: Prevents self-deactivation, audit trail preservation

### Database
- SQLite for local development
- PostgreSQL (Neon.tech) for production on Render
- Automatic schema creation on first startup
- Soft delete support for compliance and audit trails

## 🚀 Quick Start

### Local Development

1. **Clone and Setup**
   ```bash
   git clone https://github.com/jovsnewbie6/ojt-expiration-tracker.git
   cd ojt-expiration-tracker
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env for local development (defaults to SQLite)
   ```

4. **Initialize Database**
   ```bash
   python create_director.py  # Creates Director admin account
   ```

5. **Run Application**
   ```bash
   python run.py
   # App runs at http://localhost:5000
   ```

### Default Credentials (Local Development)

- **Director Admin**
  - Username: `director`
  - Password: `ChangeMe@2024`

- **Regular Admin** (optional)
  - Username: `admin`
  - Password: `admin123`

## 📦 Project Structure

```
ojt-expiration-tracker/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── models.py             # Database models (User, Student, StudentRecord)
│   ├── routes.py             # Application routes
│   ├── templates/            # HTML templates
│   │   ├── login_choice.html
│   │   ├── admin_login.html
│   │   ├── admin_dashboard.html
│   │   ├── admin_edit.html
│   │   ├── manage_students.html  # NEW: Student account management
│   │   ├── add_admin.html        # UPDATED: Admin staff management
│   │   └── ...
│   └── static/
│       └── style.css         # Styling with dark mode support
├── config.py                 # Configuration (PostgreSQL support)
├── create_director.py        # Initialize Director account
├── DEPLOYMENT.md             # Production deployment guide
├── render.yaml               # Render.com configuration
├── requirements.txt          # Python dependencies
└── .env.example              # Environment variables template
```

## 🔐 Database Models

### User (Admin)
- `id` (Primary Key)
- `username` (Unique)
- `password_hash`
- `role` (admin/staff)
- `is_active` (Soft delete support)

### Student
- `id` (Primary Key)
- `email` (Unique)
- `student_number` (Unique)
- `name`
- `year_section`
- `password_hash`
- `is_active` (Soft delete support)
- `created_at`

### StudentRecord
- `id` (Primary Key)
- `student_id` (Foreign Key)
- `name`, `course`, `year_section`
- `company_name`, `business_nature`
- `validity`, `notarized_date`
- Document tracking (resume, medical cert, MOA, insurance, etc.)
- `status` (Pending/Incomplete/Approved)
- `expiration_date`, `progress`
- `attachments` (JSON array of uploaded PDFs)

## 🌐 Deployment to Render + Neon PostgreSQL

### Prerequisites
1. GitHub repository connected to Render.com
2. Neon.tech PostgreSQL database

### Setup Steps

1. **Create Neon PostgreSQL Database**
   - Go to neon.tech, create account
   - Create a new database
   - Copy the connection string

2. **Configure Render.com**
   - Connect GitHub repository
   - Use `whigan` branch for testing or `main` for production
   - Set environment variables:
     ```
     DATABASE_URL=postgresql://user:pass@ep-xxxxx.neon.tech/dbname?sslmode=require
     SECRET_KEY=your-secure-random-key
     DIRECTOR_USERNAME=director
     DIRECTOR_PASSWORD=your-secure-password
     ```

3. **Deploy**
   - Push to `whigan` or `main` branch
   - Render automatically builds and deploys
   - Check logs in Render dashboard

4. **Post-Deployment**
   ```bash
   # SSH into Render
   python create_director.py  # Initialize Director account
   ```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed production setup.

## 🔄 Account Deactivation (Soft Delete)

Instead of permanently deleting users, accounts can be deactivated:

- **Prevents Login**: Deactivated users cannot log in
- **Preserves Data**: All records and submissions remain in database
- **Audit Trail**: Maintains compliance and historical records
- **Reactivation**: Can be reactivated at any time

### Admin Actions
1. Go to "Manage Staff" to deactivate/reactivate admins
2. Go to "Manage Students" to deactivate/reactivate students
3. Deactivated accounts appear greyed out with status badge

## 📝 API Routes

### Authentication
- `GET /login` - Login choice page (student vs admin)
- `POST /student/login` - Student login
- `POST /admin/login` - Admin login
- `GET /student/logout` - Student logout
- `GET /admin/logout` - Admin logout

### Student Portal
- `GET /student/portal` - Student dashboard
- `POST /student/register` - Register new student
- `GET /student/change-password` - Change password
- `POST /student/forgot-password` - Password reset

### Admin Dashboard
- `GET /admin/dashboard` - Admin main dashboard
- `GET /admin/edit/<record_id>` - Edit student submission
- `POST /admin/edit/<record_id>` - Update submission
- `POST /admin/delete/<record_id>` - Delete submission
- `GET /admin/create-staff` - Manage admin staff
- `GET /admin/manage-students` - Manage student accounts
- `POST /admin/toggle-user/<type>/<id>` - Deactivate/reactivate user

### Exports
- `GET /admin/download-report` - Download CSV report
- `GET /admin/export-approved` - Export approved records as Excel

## 🛠️ Technologies

- **Backend**: Python Flask
- **Database**: SQLite (dev), PostgreSQL/Neon (production)
- **ORM**: SQLAlchemy
- **Auth**: Flask-Login, Werkzeug
- **Server**: Gunicorn (production)
- **Frontend**: HTML5, CSS3 (with dark mode)
- **Deployment**: Render.com

## 📋 Requirements

See [requirements.txt](requirements.txt) for complete list:
- Flask 3.1.3
- Flask-Login 0.6.3
- Flask-SQLAlchemy 3.1.1
- SQLAlchemy 2.0.49
- psycopg2-binary 2.9.12 (PostgreSQL driver)
- Gunicorn 25.3.0
- python-dotenv 1.2.2

## 🔧 Development

### Run Tests
```bash
python -c "from app import create_app; app = create_app(); print('✓ App initialized')"
```

### Database Migrations
For schema changes, modify `app/models.py` and the database updates automatically on next startup via `db.create_all()`.

### Environment Variables
Copy `.env.example` to `.env` and customize:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## 📄 License

This project is proprietary and confidential for Poly University of the Philippines (PUP) Internal Audit Office.

## 👥 Contributors

- Development Team - PUP Information Technology Services

## 📞 Support

For issues or questions, contact the PUP Internal Audit Office or IT Services.
   ```
   npm start
   ```
2. Open your browser and navigate to `http://localhost:3000` to access the application.

### Python version

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Run the Flask app locally:
   ```
   python app.py
   ```
3. Open your browser and navigate to `http://127.0.0.1:5000`.

### Production deployment

This app is ready to deploy as a standalone website.

1. Install requirements:
   ```
   pip install -r requirements.txt
   ```
2. Start with Gunicorn:
   ```
   gunicorn app:app
   ```

#### Deploy on Render / Railway / PythonAnywhere

- Push the repo to GitHub.
- Create a new web service on Render or Railway.
- Set the start command to:
  ```
  gunicorn app:app
  ```
- Optionally use `runtime.txt` to pin Python 3.12.
- For Render, use the included `render.yaml` file so the service is configured automatically.

#### GitHub + Render

1. Install Git if needed.
2. Create a GitHub repository for this project.
3. Run `deploy.ps1` from PowerShell (or use equivalent Git commands).
4. Connect the GitHub repo in Render and select the `main` branch.
5. Render will build and deploy automatically on every push.

#### Custom domain

- Replace `your.custom.domain` in `render.yaml` with your actual domain name.
- In Render, add the same custom domain to the service settings.
- Point your domain provider DNS to Render using the records Render gives you.

#### Docker

Build and run with Docker:

```bash
docker build -t ojt-expiration-tracker .
docker run -p 5000:5000 ojt-expiration-tracker
```

Open `http://127.0.0.1:5000` once the container starts.

## Contributing

Feel free to submit issues or pull requests to improve the project. Your contributions are welcome!

## License

This project is licensed under the MIT License.