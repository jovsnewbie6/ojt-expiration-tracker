import csv
import io
import json
import os
import re
import uuid
import logging
from collections import defaultdict
from datetime import datetime

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from functools import wraps
from sqlalchemy import func
from werkzeug.utils import secure_filename

from app import db
from app.decorators import permission_required
from app.models import Permission, StudentRecord, User, Student

# Configure logging
logger = logging.getLogger(__name__)

main_bp = Blueprint("main", __name__)

REQUIREMENT_FIELDS = [
    ("has_resume", "Resume"),
    ("has_med_cert", "Medical Certificate"),
    ("has_consent_form", "Consent Form"),
    ("has_moa", "MOA"),
    ("has_insurance", "Insurance"),
    ("has_intent_letter", "Intent Letter"),
    ("has_endorsement_letter", "Endorsement Letter"),
]


@main_bp.before_request
def ensure_database_connection():
    """Ensure database connection is alive before processing request."""
    from sqlalchemy.exc import OperationalError
    from sqlalchemy import text

    try:
        # Test the connection with a simple ping
        db.session.execute(text("SELECT 1"))

    except OperationalError:
        logger.warning("Database connection lost, disposing pool and retrying...")

        # Dispose of the engine to force a new connection
        db.engine.dispose()

        try:
            db.session.execute(text("SELECT 1"))
            logger.info("Database connection re-established successfully")

        except Exception as e:
            logger.error(f"Could not re-establish database connection: {str(e)}", exc_info=True)

    except Exception as e:
        logger.warning(f"Non-critical error in before_request: {str(e)}", exc_info=True)


@main_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for monitoring and debugging."""
    try:
        from sqlalchemy import text
        # Try to query the database
        db.session.execute(text("SELECT 1"))
        db.session.commit()
        return {
            "status": "healthy",
            "database": "connected"
        }, 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }, 500
    
@main_bp.route("/check-attendance", methods=["GET"])
def check_attendance():
    """Debug route to verify Attendance table exists."""
    try:
        from sqlalchemy import text

        result = db.session.execute(
            text("SELECT COUNT(*) FROM attendance")
        )

        count = result.scalar()

        return {
            "status": "success",
            "message": "Attendance table exists",
            "record_count": count
        }, 200

    except Exception as e:
        logger.error(
            f"Attendance table check failed: {str(e)}",
            exc_info=True
        )

        return {
            "status": "error",
            "message": str(e)
        }, 500

def parse_integer(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def allowed_file(filename):
    if not filename:
        return False
    # Restrict to PDF only for storage efficiency
    allowed_extensions = {"pdf"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def save_attachments(record, files):
    if not files:
        return []
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    record_folder = os.path.join(upload_folder, f"record_{record.id}")
    os.makedirs(record_folder, exist_ok=True)

    saved_files = []
    for file in files:
        if file and allowed_file(file.filename):
            original_name = secure_filename(file.filename)
            unique_name = f"{uuid.uuid4().hex}_{original_name}"
            target_path = os.path.join(record_folder, unique_name)
            file.save(target_path)
            saved_files.append({"original": original_name, "filename": unique_name})
    return saved_files


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please sign in as an admin to access that page.", "error")
            return redirect(url_for("main.admin_login"))

        if not getattr(current_user, "is_admin", False):
            flash("Admin access is required to view that page.", "error")
            return redirect(url_for("main.admin_login"))

        return view(*args, **kwargs)

    return wrapped


def staff_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please sign in to access that page.", "error")
            return redirect(url_for("main.student_login"))

        if getattr(current_user, "is_admin", False) or getattr(current_user, "role", None) in {"coordinator", "faculty"}:
            return view(*args, **kwargs)

        flash("Staff access is required to view that page.", "error")
        return redirect(url_for("main.student_portal"))

    return wrapped


@main_bp.route("/login")
def login_choice():
    if current_user.is_authenticated:
        if isinstance(current_user, Student):
            return redirect(url_for("main.student_portal"))
        elif current_user.is_admin:
            return redirect(url_for("main.admin_dashboard"))
    return render_template("login_choice.html")


def _find_student_records(name, year_section):
    return (
        StudentRecord.query
        .filter(func.lower(StudentRecord.name) == name.lower())
        .filter(func.lower(StudentRecord.year_section) == year_section.lower())
        .order_by(StudentRecord.expiration_date)
    )


@main_bp.route("/attachment/<int:record_id>/<path:filename>")
def attachment_download(record_id, filename):
    record_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], f"record_{record_id}")
    return send_from_directory(record_folder, filename, as_attachment=True)


@main_bp.route("/")
@main_bp.route("/index")
@main_bp.route("/index.html")
def home():
    return redirect(url_for("main.student_portal"))


@main_bp.route("/student", methods=["GET", "POST"])
@login_required
def student_portal():
    # Prevent admins from accessing student portal
    if not isinstance(current_user, Student):
        flash("Admins cannot access the student portal.", "error")
        return redirect(url_for("main.admin_dashboard"))

    # Fetch only records for the current student
    student_records = StudentRecord.query.filter_by(student_id=current_user.id).order_by(StudentRecord.expiration_date).all()

    if request.method == "POST":
        action = request.form.get("action", "submit")
        company_name = request.form.get("company_name", "").strip()
        business_nature = request.form.get("business_nature", "").strip()
        validity = request.form.get("validity", "").strip()
        notarized_date_text = request.form.get("notarized_date", "")
        expiration_date_text = request.form.get("expiration_date", "")
        attachments = request.files.getlist("attachments")
        has_resume = bool(request.form.get("has_resume"))
        has_med_cert = bool(request.form.get("has_med_cert"))
        has_consent_form = bool(request.form.get("has_consent_form"))
        has_moa = bool(request.form.get("has_moa"))
        has_insurance = bool(request.form.get("has_insurance"))
        has_intent_letter = bool(request.form.get("has_intent_letter"))
        has_endorsement_letter = bool(request.form.get("has_endorsement_letter"))

        if action == "submit":
            if not company_name or not business_nature or not validity or not expiration_date_text:
                flash("Please complete the required submission fields.", "error")
            else:
                try:
                    expiration_date = datetime.strptime(expiration_date_text, "%Y-%m-%d").date()
                except ValueError:
                    flash("Please enter a valid expiration date.", "error")
                    return redirect(url_for("main.student_portal"))

                notarized_date = None
                if notarized_date_text:
                    try:
                        notarized_date = datetime.strptime(notarized_date_text, "%Y-%m-%d").date()
                    except ValueError:
                        flash("Please enter a valid notarized date.", "error")
                        return redirect(url_for("main.student_portal"))

                record = StudentRecord(
                    student_id=current_user.id,
                    name=current_user.name,
                    course="",
                    year_section=current_user.year_section,
                    company_name=company_name,
                    business_nature=business_nature,
                    validity=validity,
                    notarized_date=notarized_date,
                    expiration_date=expiration_date,
                    status="Pending",
                    has_resume=has_resume,
                    has_med_cert=has_med_cert,
                    has_consent_form=has_consent_form,
                    has_moa=has_moa,
                    has_insurance=has_insurance,
                    has_intent_letter=has_intent_letter,
                    has_endorsement_letter=has_endorsement_letter,
                    is_complete=(has_resume and has_med_cert and has_consent_form and has_moa and has_insurance and has_intent_letter and has_endorsement_letter),
                    comments="",
                )
                db.session.add(record)
                db.session.commit()

                # Calculate initial progress
                record.progress = record.calculate_progress()
                
                if attachments:
                    saved = save_attachments(record, attachments)
                    if saved:
                        record.attachments = json.dumps(saved)
                
                db.session.commit()

                flash("Your submission is now pending review. Admin will update your status.", "success")
                student_records = StudentRecord.query.filter_by(student_id=current_user.id).order_by(StudentRecord.expiration_date).all()

    return render_template(
        "index.html",
        student_records=student_records,
        requirement_fields=REQUIREMENT_FIELDS,
        form_action=url_for("main.student_portal"),
        student_filters={},
        is_admin=False,
        getattr_fn=getattr,
    )


@main_bp.route("/student/register", methods=["GET", "POST"])
def student_register():
    if current_user.is_authenticated:
        return redirect(url_for("main.student_portal"))

    if request.method == "POST":
        # Ensure database is ready
        from app.database_init import ensure_database_ready
        if not ensure_database_ready():
            logger.error("Database not ready during registration")
            flash("Database not ready. Please try again in a moment.", "error")
            return render_template("register.html")

        student_number = request.form.get("student_number", "").strip()
        full_name = request.form.get("full_name", "").strip()
        year_section = request.form.get("year_section", "").strip()
        email = request.form.get("email", "").strip() # Capture email
        password = request.form.get("password", "").strip()

        if not student_number or not full_name or not year_section or not email or not password:
            flash("Please complete all registration fields.", "error")
            return render_template("register.html")

        # Check if student already exists
        try:
            existing_student = Student.query.filter_by(student_number=student_number).first()
            logger.info(f"Query result for existing student: {existing_student}")
            if existing_student:
                flash("That student number is already registered.", "error")
                return render_template("register.html")
        except Exception as e:
            logger.error("Database error during registration duplicate check", exc_info=True)
            # Try to identify the specific issue
            error_str = str(e).lower()
            if "connection" in error_str or "timeout" in error_str:
                flash("Database connection error. Please try again.", "error")
            elif "table" in error_str or "does not exist" in error_str:
                logger.error("Tables not found - attempting to initialize")
                if ensure_database_ready():
                    flash("Database initialized. Please try registering again.", "success")
                else:
                    flash("Database error. Please contact support.", "error")
            else:
                flash("An error occurred. Please try again.", "error")
            return render_template("register.html")

        # Create and save new student
        try:
            student = Student(
                username=student_number, # Setting username to student_number
                student_number=student_number,
                name=full_name,
                year_section=year_section,
                email=email # Saving email
            )
            logger.info(f"Setting password for student: {student_number}")
            student.set_password(password)
            db.session.add(student)
            logger.info(f"Flushing student {student_number} to detect constraint violations...")
            db.session.flush()  # Flush to detect constraint violations early
            logger.info(f"Committing student {student_number} to database...")
            db.session.commit()
            
            logger.info("Student registration successful")
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("main.student_login"))
        except Exception as e:
            db.session.rollback()
            logger.error("Error during student registration", exc_info=True)
            
            # Provide more specific error messages
            error_msg = str(e).lower()
            if "unique" in error_msg or "duplicate" in error_msg:
                flash("This student number is already registered.", "error")
            elif "constraint" in error_msg:
                flash("Invalid data provided. Please check your inputs.", "error")
            else:
                flash("An error occurred during registration. Please try again.", "error")
            
            return render_template("register.html")

    return render_template("register.html")


@main_bp.route("/admin/create-staff", methods=["GET", "POST"])
@login_required
@admin_required
def admin_create_staff():
    if not current_user.is_admin:
        abort(403)

    if request.method == "POST":
        try:
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            selected_permissions = request.form.getlist("permissions")

            if not username or not password:
                flash("Please provide both a username and password.", "error")
                return render_template("add_admin.html", admins=User.query.filter_by(role="admin").all())

            if User.query.filter_by(username=username).first():
                flash("That admin username is already taken.", "error")
                return render_template("add_admin.html", admins=User.query.filter_by(role="admin").all())

            admin = User(username=username, role="admin", is_active=True)
            admin.set_password(password)
            
            # Append selected permissions to the new staff member
            if selected_permissions:
                for perm_name in selected_permissions:
                    perm_object = Permission.query.filter_by(name=perm_name).first()
                    if perm_object:
                        admin.permissions.append(perm_object)
            
            db.session.add(admin)
            db.session.commit()

            flash("New admin user created successfully.", "success")
            return redirect(url_for("main.admin_create_staff"))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating admin user: {str(e)}")
            flash("An error occurred while creating the admin user. Please try again.", "error")
            return render_template("add_admin.html", admins=User.query.filter_by(role="admin").all())

    admins = User.query.filter_by(role="admin").all()
    return render_template("add_admin.html", admins=admins)


@main_bp.route("/student/login", methods=["GET", "POST"])
def student_login():
    if current_user.is_authenticated:
        return redirect(url_for("main.student_portal"))

    if request.method == "POST":
        try:
            student_number = request.form.get("student_number", "").strip()
            password = request.form.get("password", "").strip()
            
            if not student_number or not password:
                flash("Please provide both student number and password.", "error")
                return render_template("student_login.html")
            
            # Search by student_number, as this is the primary identifier for students
            student = Student.query.filter_by(student_number=student_number).first()

            if student and student.check_password(password):
                # Check if account is active
                if not student.is_active:
                    logger.warning(f"Login attempt for deactivated account: {student_number}")
                    flash("This account has been deactivated. Please contact support.", "error")
                    return render_template("student_login.html")
                
                login_user(student)
                logger.info(f"Student login successful: {student_number}")
                flash("Login successful.", "success")
                
                # Role-based redirection
                if student.role != "student":
                    return redirect(url_for("main.admin_dashboard"))
                return redirect(url_for("main.student_portal"))
            else:
                logger.warning(f"Failed login attempt for: {student_number}")
                flash("Invalid student number or password.", "error")
                
        except Exception as e:
            logger.error(f"Error during student login: {str(e)}", exc_info=True)
            flash("An internal error occurred. Please try again.", "error")

    return render_template("student_login.html")


@main_bp.route("/student/logout")
@login_required
def student_logout():
    if isinstance(current_user, Student):
        logout_user()
        flash("Student signed out.", "success")
        return redirect(url_for("main.student_login"))
    return redirect(url_for("main.admin_dashboard"))


@main_bp.route("/student/change-password", methods=["GET", "POST"])
@login_required
def student_change_password():
    if not isinstance(current_user, Student):
        flash("Only students can change their password from this page.", "error")
        return redirect(url_for("main.student_portal"))

    if request.method == "POST":
        current_password = request.form.get("current_password", "").strip()
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not current_password or not new_password or not confirm_password:
            flash("Please complete all password fields.", "error")
            return render_template("student_change_password.html")

        if not current_user.check_password(current_password):
            flash("Your current password is incorrect.", "error")
            return render_template("student_change_password.html")

        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return render_template("student_change_password.html")

        if len(new_password) < 6:
            flash("New password must be at least 6 characters long.", "error")
            return render_template("student_change_password.html")

        current_user.set_password(new_password)
        db.session.commit()

        flash("Your password has been changed successfully.", "success")
        return redirect(url_for("main.student_portal"))

    return render_template("student_change_password.html")


@main_bp.route("/student/forgot-password", methods=["GET", "POST"])
def student_forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.student_portal"))

    if request.method == "POST":
        # Check database connection first
        from app.decorators import check_database_connection
        db_connected, db_error = check_database_connection()
        if not db_connected:
            logger.error(f"Database connection failed during password reset: {db_error}")
            error_detail = (db_error[:50] if db_error else "Unknown error")
            flash(f"Database connection error. Please try again. (Error: {error_detail})", "error")
            return render_template("student_forgot_password.html")

        student_number = request.form.get("student_number", "").strip()
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not student_number or not new_password or not confirm_password:
            flash("Please complete all fields.", "error")
            return render_template("student_forgot_password.html")

        if new_password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("student_forgot_password.html")

        if len(new_password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return render_template("student_forgot_password.html")

        # Find student
        try:
            logger.info(f"Looking up student with number: {student_number}")
            student = Student.query.filter_by(student_number=student_number).first()
            logger.info(f"Student lookup result: {student}")
            if not student:
                logger.warning(f"Password reset attempt for non-existent student: {student_number}")
                flash("Student number not found.", "error")
                return render_template("student_forgot_password.html")
        except Exception as e:
            logger.error(f"Database error finding student {student_number}: {str(e)}", exc_info=True)
            logger.error(f"Exception type: {type(e).__name__}")
            error_str = str(e).lower()
            if "connection" in error_str or "timeout" in error_str or "pool" in error_str:
                flash("Database connection error. Please try again.", "error")
            elif "table" in error_str or "does not exist" in error_str:
                flash("System error: database not initialized. Contact support.", "error")
            else:
                flash("Database error. Please try again or contact support.", "error")
            return render_template("student_forgot_password.html")

        # Update password
        try:
            logger.info(f"Updating password for student: {student_number}")
            student.set_password(new_password)
            db.session.flush()  # Flush to detect issues early
            logger.info(f"Password updated in session for student: {student_number}, committing...")
            db.session.commit()
            logger.info(f"Commit successful for student: {student_number}")
            
            logger.info(f"Password reset successful for student: {student_number}")
            flash("Your password has been reset successfully. Please log in.", "success")
            return redirect(url_for("main.student_login"))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating password for student {student_number}", exc_info=True)
            logger.error(f"Exception type: {type(e).__name__}, Details: {str(e)}")
            error_str = str(e).lower()
            if "connection" in error_str or "timeout" in error_str:
                flash("Database connection error. Please try again.", "error")
            else:
                flash("An error occurred while resetting your password. Please try again or contact support.", "error")
            return render_template("student_forgot_password.html")

    return render_template("student_forgot_password.html")


@main_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    # Only redirect if they are already logged in AND active
    if current_user.is_authenticated and current_user.is_active:
        return redirect(url_for("main.admin_dashboard"))
    
    # ... rest of your login logic ...

    if request.method == "POST":
        # Check database connection first
        from app.decorators import check_database_connection
        db_connected, db_error = check_database_connection()
        if not db_connected:
            logger.error("Database connection failed during admin login")
            flash("Database connection error. Please try again.", "error")
            return render_template("admin_login.html", is_admin=current_user.is_authenticated)
        
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        if not username or not password:
            flash("Please provide both username and password.", "error")
            return render_template("admin_login.html", is_admin=current_user.is_authenticated)
        
        # Query for admin user
        try:
            logger.info(f"Looking up admin user: {username}")
            admin = User.query.filter_by(username=username, role="admin").first()
            logger.info(f"Admin user lookup result: {admin}")

            if admin and admin.check_password(password):
                # Check if account is active
                if not admin.is_active:
                    logger.warning("Login attempt for deactivated admin account")
                    flash("This account has been deactivated. Please contact support.", "error")
                    return render_template("admin_login.html", is_admin=current_user.is_authenticated)
                
                login_user(admin)
                logger.info("Admin login successful")
                flash("Admin signed in successfully.", "success")
                return redirect(url_for("main.admin_dashboard"))
            else:
                logger.warning("Failed admin login attempt")
                flash("Invalid admin credentials.", "error")
        except Exception as e:
            logger.error("Database error during admin login", exc_info=True)
            error_str = str(e).lower()
            if "connection" in error_str or "timeout" in error_str or "pool" in error_str:
                flash("Database connection error. Please try again.", "error")
            elif "table" in error_str or "does not exist" in error_str:
                flash("System error: database not initialized. Contact support.", "error")
            else:
                flash("An error occurred during login. Please try again.", "error")

    return render_template(
        "admin_login.html",
        is_admin=current_user.is_authenticated,
    )


@main_bp.route("/admin/logout")
@login_required
def admin_logout():
    logout_user()
    flash("Signed out successfully.", "success")
    return redirect(url_for("main.login_choice"))


@main_bp.route("/admin/dashboard")
@login_required
@staff_required
def admin_dashboard():
    search_term = request.args.get("search", "").strip()
    records_query = StudentRecord.query.order_by(StudentRecord.expiration_date)
    records = records_query.all()  # Fetch all records first to avoid multiple queries in the loop below

    if search_term:
        records_query = records_query.filter(func.lower(StudentRecord.name).contains(search_term.lower()))

    records = records_query.all()
    grouped_records = {}
    for record in records:
        year_label = record.year_only or "N/A"
        section_label = record.section_only or "N/A"
        grouped_records.setdefault(year_label, {}).setdefault(section_label, []).append(record)

    grouped_records = {
        year: {
            section: grouped_records[year][section]
            for section in sorted(grouped_records[year].keys(), key=str.lower)
        }
        for year in sorted(grouped_records.keys(), key=str.lower)
    }

    totals = {
        "pending": StudentRecord.query.filter_by(status="Pending").count(),
        "incomplete": StudentRecord.query.filter_by(status="Incomplete").count(),
        "approved": StudentRecord.query.filter_by(status="Approved").count(),
        "practicum_visited": StudentRecord.query.filter_by(status="Practicum Visited").count(),
    }
    return render_template(
        "admin_dashboard.html",
        records=records,
        grouped_records=grouped_records,
        totals=totals,
        requirement_fields=REQUIREMENT_FIELDS,
        search_term=search_term,
        is_admin=current_user.is_authenticated,
    )


@main_bp.route("/admin/permissions")
@login_required
@admin_required
def admin_permissions():
    users = User.query.order_by(User.username).all()
    permissions = Permission.query.order_by(Permission.name).all()
    return render_template(
        "admin_permissions.html",
        users=users,
        permissions=permissions,
        is_admin=current_user.is_authenticated,
    )


@main_bp.route("/admin/update-permissions", methods=["POST"])
@login_required
@admin_required
def admin_update_permissions():
    users = User.query.order_by(User.username).all()
    permissions = Permission.query.order_by(Permission.id).all()

    for user in users:
        # Reset this user's permissions, then apply selections from the submitted grid.
        user.permissions = []
        for permission in permissions:
            checkbox_name = f"permission_{user.id}_{permission.id}"
            if request.form.get(checkbox_name):
                user.permissions.append(permission)

    db.session.commit()
    flash("Permissions have been updated successfully.", "success")
    return redirect(url_for("main.admin_permissions"))


@main_bp.route("/admin/edit/<int:record_id>", methods=["GET", "POST"])
@login_required
@staff_required
def admin_edit(record_id):
    record = StudentRecord.query.get_or_404(record_id)

    if request.method == "POST":
        record.name = request.form.get("name", record.name).strip()
        record.year_section = request.form.get("year_section", record.year_section).strip()
        record.company_name = request.form.get("company_name", record.company_name).strip()
        record.business_nature = request.form.get("business_nature", record.business_nature).strip()
        record.validity = request.form.get("validity", record.validity).strip()
        record.status = request.form.get("status", record.status)
        record.comments = request.form.get("comments", "").strip()
        
        record.has_resume = bool(request.form.get("has_resume"))
        record.has_med_cert = bool(request.form.get("has_med_cert"))
        record.has_consent_form = bool(request.form.get("has_consent_form"))
        record.has_moa = bool(request.form.get("has_moa"))
        record.has_insurance = bool(request.form.get("has_insurance"))
        record.has_intent_letter = bool(request.form.get("has_intent_letter"))
        record.has_endorsement_letter = bool(request.form.get("has_endorsement_letter"))

        # Calculate progress based on completed requirements
        record.progress = record.calculate_progress()

        attachments = request.files.getlist("attachments")
        if attachments:
            saved = save_attachments(record, attachments)
            if saved:
                existing = record.attachment_items
                existing.extend(saved)
                record.attachments = json.dumps(existing)

        record.is_complete = record.has_all_requirements

        expiration_date_text = request.form.get("expiration_date", "")
        if expiration_date_text:
            try:
                record.expiration_date = datetime.strptime(expiration_date_text, "%Y-%m-%d").date()
            except ValueError:
                flash("Please enter a valid expiration date.", "error")
                return redirect(url_for("main.admin_edit", record_id=record_id))

        db.session.commit()
        flash("Record updated successfully.", "success")
        return redirect(url_for("main.admin_dashboard"))

    return render_template(
        "admin_edit.html",
        record=record,
        requirement_fields=REQUIREMENT_FIELDS,
        is_admin=current_user.is_authenticated,
    )


@main_bp.route("/admin/delete/<int:record_id>", methods=["POST"])
@login_required
@staff_required
def admin_delete(record_id):
    record = StudentRecord.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    flash("Submission removed successfully.", "success")
    return redirect(url_for("main.admin_dashboard"))


@main_bp.route("/admin/toggle-user/<string:user_type>/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def toggle_user_status(user_type, user_id):
    """Toggle user active status (soft delete). Only admins can deactivate users."""
    
    try:
        # Prevent director from deactivating their own account
        if user_type == "admin" and current_user.id == user_id:
            flash("You cannot deactivate your own account.", "error")
            return redirect(request.referrer or url_for("main.admin_dashboard"))
        
        if user_type == "admin":
            user = User.query.get_or_404(user_id)
            user.is_active = not user.is_active
            action = "deactivated" if not user.is_active else "reactivated"
            logger.info(f"Admin account '{user.username}' (ID: {user_id}) has been {action}")
            flash(f"Admin account '{user.username}' has been {action}.", "success")
        elif user_type == "student":
            student = Student.query.get_or_404(user_id)
            student.is_active = not student.is_active
            action = "deactivated" if not student.is_active else "reactivated"
            logger.info(f"Student account '{student.name}' ({student.student_number}) has been {action}")
            flash(f"Student account '{student.name}' ({student.student_number}) has been {action}.", "success")
        else:
            flash("Invalid user type.", "error")
            return redirect(request.referrer or url_for("main.admin_dashboard"))
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error toggling user status for {user_type} ID {user_id}: {str(e)}")
        current_app.logger.error(f"Error toggling user status: {str(e)}", exc_info=True)
        flash("An error occurred while updating user status. Please try again or contact support.", "error")
    
    return redirect(request.referrer or url_for("main.admin_dashboard"))


def normalize_year_section(section):
    if not section:
        return "Unassigned"

    normalized = re.sub(r"\s+DIT\s*$", "", section.strip(), flags=re.IGNORECASE)
    normalized = normalized.strip()

    if normalized.lower().startswith("3-"):
        section_part = normalized.split()[0]
        return section_part.upper()

    return normalized


@main_bp.route("/admin/manage-students")
@login_required
@staff_required
def admin_manage_students():
    """Display and manage student account status."""
    # Check database connection first
    from app.decorators import check_database_connection
    db_connected, db_error = check_database_connection()
    if not db_connected:
        logger.error(f"Database connection failed in manage_students: {db_error}")
        error_detail = (db_error[:50] if db_error else "Unknown error")
        flash(f"Database connection error. Please try again. (Error: {error_detail})", "error")
        return redirect(url_for("main.admin_dashboard"))

    try:
        # Fetch students with error handling
        try:
            logger.info("Fetching all students from database...")
            students = Student.query.order_by(Student.name).all()
            logger.info(f"Successfully fetched {len(students)} students")
        except Exception as e:
            logger.error(f"Database error fetching students: {str(e)}", exc_info=True)
            logger.error(f"Exception type: {type(e).__name__}")
            # Identify specific database issues
            error_str = str(e).lower()
            if "connection" in error_str or "timeout" in error_str or "pool" in error_str:
                flash("Database connection error. The system is temporarily unavailable. Please try again.", "error")
                logger.error(f"Connection pool or timeout issue detected: {error_str}")
            elif "table" in error_str or "does not exist" in error_str:
                flash("System error: students table not found. Contact support.", "error")
                logger.error(f"Table doesn't exist: {error_str}")
            else:
                flash("Error fetching student data. Please try again or contact support.", "error")
            return redirect(url_for("main.admin_dashboard"))
        
        # Group students by section
        try:
            section_groups = defaultdict(list)
            for student in students:
                section_key = normalize_year_section(student.year_section)
                section_groups[section_key].append(student)

            ordered_section_groups = sorted(
                section_groups.items(),
                key=lambda item: item[0].lower(),
            )
        except Exception as e:
            logger.error(f"Error grouping students: {str(e)}", exc_info=True)
            flash("Error processing student data. Please try again or contact support.", "error")
            return redirect(url_for("main.admin_dashboard"))

        return render_template(
            "manage_students.html",
            section_groups=ordered_section_groups,
        )
    except Exception as e:
        logger.error(f"Unexpected error in manage_students: {str(e)}", exc_info=True)
        logger.error(f"Exception type: {type(e).__name__}")
        flash("An error occurred while loading the student management page. Please try again or contact support.", "error")
        return redirect(url_for("main.admin_dashboard"))


@main_bp.route("/admin/manage-staff")
@login_required
@admin_required
def admin_manage_staff():
    """Display and manage staff (admin/faculty/coordinator) account roles and permissions."""
    users = User.query.order_by(User.id.desc()).all()
    return render_template("manage_staff.html", users=users)


@main_bp.route("/admin/edit-user-access", methods=["POST"])
@main_bp.route("/admin/edit-user-access/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def edit_user_access(user_id=None):
    """Update a user's role and permissions."""
    if user_id is None:
        user_id_str = request.form.get("user_id", "").strip()
        if not user_id_str.isdigit():
            flash("No user selected for access modification.", "error")
            return redirect(url_for("main.admin_manage_staff"))
        user_id = int(user_id_str)

    user = User.query.get_or_404(user_id)
    
    try:
        # Prevent editing own account
        if current_user.id == user_id:
            flash("You cannot modify your own account access.", "error")
            return redirect(url_for("main.admin_manage_staff"))
        
        # Update role
        new_role = request.form.get("role", "").strip()
        if new_role not in ["student", "faculty", "coordinator", "admin"]:
            flash("Invalid role selected.", "error")
            return redirect(url_for("main.admin_manage_staff"))
        
        user.role = new_role
        
        # Clear existing permissions and add new ones
        selected_permissions = request.form.getlist("permissions")
        user.permissions.clear()
        
        if selected_permissions:
            for perm_name in selected_permissions:
                perm_object = Permission.query.filter_by(name=perm_name).first()
                if perm_object:
                    user.permissions.append(perm_object)
        
        db.session.commit()
        flash(f"User '{user.username}' access updated successfully.", "success")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user access: {str(e)}")
        flash("An error occurred while updating user access. Please try again.", "error")
    
    return redirect(url_for("main.admin_manage_staff"))


@main_bp.route("/admin/modify-student-access", methods=["POST"])
@main_bp.route("/admin/modify-student-access/<int:student_id>", methods=["POST"])
@login_required
@admin_required
def modify_student_access(student_id=None):
    """Update a student's role and permissions (promotion to faculty/coordinator)."""
    if student_id is None:
        student_id_str = request.form.get("student_id", "").strip()
        if not student_id_str.isdigit():
            flash("No student selected for access modification.", "error")
            return redirect(url_for("main.admin_manage_students"))
        student_id = int(student_id_str)

    try:
        student = Student.query.get_or_404(student_id)
        
        # Update role
        new_role = request.form.get("role", "").strip()
        if new_role not in ["student", "faculty", "coordinator"]:
            flash("Invalid role selected.", "error")
            return redirect(url_for("main.admin_manage_students"))
        
        student.role = new_role
        
        # Clear existing permissions and add new ones
        selected_permissions = request.form.getlist("permissions")
        student.permissions.clear()
        
        if selected_permissions:
            for perm_name in selected_permissions:
                perm_object = Permission.query.filter_by(name=perm_name).first()
                if perm_object:
                    student.permissions.append(perm_object)
        
        db.session.commit()
        logger.info(f"Student '{student.name}' (ID: {student_id}) access updated to role: {new_role}")
        flash(f"Student '{student.name}' access updated successfully.", "success")
        
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error updating student access for ID {student_id}: {str(e)}")
        current_app.logger.error(f"Error updating student access: {str(e)}", exc_info=True)
        flash("An error occurred while updating student access. Please try again or contact support.", "error")
    
    return redirect(url_for("main.admin_manage_students"))


@main_bp.route("/admin/download-report")
@login_required
@staff_required
def admin_download_report():
    records = StudentRecord.query.order_by(StudentRecord.expiration_date).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Student",
        "Year / Section",
        "Company Name",
        "Business Nature",
        "Validity",
        "Notarized Date",
        "Status",
        "Expiration Date",
        "Days Left",
    ])
    for record in records:
        writer.writerow([
            record.name,
            record.display_year_section,
            record.company_name,
            record.business_nature,
            record.validity,
            record.notarized_date.strftime("%Y-%m-%d") if record.notarized_date else "",
            record.status,
            record.expiration_date.strftime("%Y-%m-%d"),
            record.days_left,
        ])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        as_attachment=True,
        download_name="admin_moa_report.csv",
        mimetype="text/csv",
    )


@main_bp.route("/admin/export-approved")
@login_required
@staff_required
def export_approved():
    approved_records = StudentRecord.query.filter(StudentRecord.status.in_(["Approved", "Practicum Visited"]))
    approved_records = approved_records.order_by(StudentRecord.expiration_date).all()

    if not approved_records:
        flash("There are no approved submissions to export.", "error")
        return redirect(url_for("main.admin_dashboard"))

    try:
        import pandas as pd
    except ImportError:
        flash("Pandas is required to export to Excel. Install it in your environment.", "error")
        return redirect(url_for("main.admin_dashboard"))

    data = []
    for record in approved_records:
        data.append({
            "Student": record.name,
            "Year / Section": record.display_year_section,
            "Company": record.company_name,
            "Business": record.business_nature,
            "Validity": record.validity,
            "Notarized Date": record.notarized_date.strftime("%Y-%m-%d") if record.notarized_date else "",
            "Status": record.status,
            "Expiration Date": record.expiration_date.strftime("%Y-%m-%d"),
            "Days Left": record.days_left,
        })

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Approved")

    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="approved_submissions.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

@main_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # 1. Validation
        if not check_password_hash(current_user.password_hash, old_password):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('main.change_password'))

        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return redirect(url_for('main.change_password'))

        # 2. Update the password (Works for both Admin and Student automatically)
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()

        flash('Your password has been updated!', 'success')
        
        # Redirect based on who they are
        if hasattr(current_user, 'student_number'):
            return redirect(url_for('main.student_portal'))
        return redirect(url_for('main.admin_dashboard'))

    return render_template('change_password.html')

@main_bp.route('/delete-student/<int:id>', methods=['POST'])
@login_required
def delete_student(id):
    # Security: Ensure only admins can delete
    if not current_user.is_admin: # Assuming you have an is_admin flag
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash(f'Account for {student.student_number} has been removed.', 'success')
    return redirect(url_for('main.admin_dashboard'))

@main_bp.route('/delete-admin/<int:id>', methods=['POST'])
@login_required
def delete_admin(id):
    if not current_user.is_admin:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    # Prevent the Director from deleting themselves!
    if current_user.id == id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('main.admin_dashboard'))

    admin = Admin.query.get_or_404(id)
    db.session.delete(admin)
    db.session.commit()
    flash('Admin account removed.', 'success')
    return redirect(url_for('main.admin_dashboard'))


# ==================== ATTENDANCE SECTION ====================

@main_bp.route("/student/attendance", methods=["GET", "POST"])
@login_required
def student_attendance():
    """Student attendance submission page"""
    # Only allow students
    if not isinstance(current_user, Student):
        flash("Only students can access this page.", "error")
        return redirect(url_for("main.admin_dashboard"))
    
    if request.method == "POST":
        try:
            from app.models import Attendance
            from datetime import datetime
            
            # Get form data
            now = datetime.now()
            attendance_date = now.date().isoformat()  # Use current date
            attendance_time = now.time().strftime("%H:%M:%S")  # Use current time
            status = request.form.get("status", "Present").strip()
            
            # Validate
            if not attendance_date or not attendance_time:
                flash("Please fill in date and time.", "error")
                return render_template("student_attendance.html")
            
            if status not in ["Present", "Absent"]:
                status = "Present"
            
            # Create attendance record
            attendance = Attendance(
                student_id=current_user.id,
                student_name=current_user.name,
                student_section=current_user.year_section or "N/A",
                attendance_date=now.date(),
                attendance_time=now.time().strftime("%H:%M:%S"),
                status=status
            )
            
            db.session.add(attendance)
            db.session.commit()
            
            flash("✓ Attendance submitted successfully.", "success")
            return redirect(url_for("main.student_attendance"))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Attendance submission error: {str(e)}", exc_info=True)
            flash("Error submitting attendance. Please try again.", "error")
            return render_template("student_attendance.html")
    
    return render_template("student_attendance.html", student=current_user)


@main_bp.route("/student/attendance/export")
@login_required
def student_attendance_export():
    """Export student attendance records to Excel"""
    if not isinstance(current_user, Student):
        flash("Only students can export attendance.", "error")
        return redirect(url_for("main.admin_dashboard"))
    
    try:
        from app.models import Attendance
        import pandas as pd
        
        # Get all attendance records for this student
        records = Attendance.query.filter_by(student_id=current_user.id).order_by(Attendance.attendance_date.desc()).all()
        
        if not records:
            flash("No attendance records to export.", "error")
            return redirect(url_for("main.student_attendance"))
        
        # Prepare data
        data = []
        for record in records:
            data.append({
                "Student Name": record.student_name,
                "Date": record.attendance_date.strftime("%Y-%m-%d"),
                "Time": record.attendance_time,
                "Status": record.status,
            })
        
        # Create Excel
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Attendance")
        
        output.seek(0)
        return send_file(
            output,
            as_attachment=True,
            download_name="my_attendance.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        
    except Exception as e:
        logger.error(f"Attendance export error: {str(e)}", exc_info=True)
        flash("Error exporting attendance. Please try again.", "error")
        return redirect(url_for("main.student_attendance"))


@main_bp.route("/admin/attendance")
@login_required
@admin_required
def admin_attendance():
    """Admin attendance view with year filter"""
    from app.models import Attendance
    
    # Get selected year from query params
    selected_year = request.args.get("year", "").strip()
    
    # Get all unique years from attendance records
    all_records = Attendance.query.all()
    years = sorted(set([str(r.attendance_date.year) for r in all_records]), reverse=True)
    
    # Filter by year if selected
    if selected_year:
        records = Attendance.query.filter(
            db.extract('year', Attendance.attendance_date) == int(selected_year)
        ).order_by(Attendance.attendance_date.desc(), Attendance.attendance_time.desc()).all()
    else:
        records = Attendance.query.order_by(Attendance.attendance_date.desc(), Attendance.attendance_time.desc()).all()
    
    return render_template("admin_attendance.html", records=records, years=years, selected_year=selected_year)


@main_bp.route("/admin/attendance/export")
@login_required
@admin_required
def admin_attendance_export():
    """Export all attendance records to Excel"""
    from app.models import Attendance
    
    try:
        import pandas as pd
        
        # Get filter year if any
        selected_year = request.args.get("year", "").strip()
        
        if selected_year:
            records = Attendance.query.filter(
                db.extract('year', Attendance.attendance_date) == int(selected_year)
            ).order_by(Attendance.attendance_date.desc()).all()
        else:
            records = Attendance.query.order_by(Attendance.attendance_date.desc()).all()
        
        if not records:
            flash("No attendance records to export.", "error")
            return redirect(url_for("main.admin_attendance"))
        
        # Prepare data
        data = []
        for record in records:
            data.append({
                "Student Name": record.student_name,
                "Date": record.attendance_date.strftime("%Y-%m-%d"),
                "Time": record.attendance_time,
                "Status": record.status,
                "Section": record.student_section,
            })
        
        # Create Excel
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Attendance")
        
        output.seek(0)
        year_label = f"_{selected_year}" if selected_year else ""
        return send_file(
            output,
            as_attachment=True,
            download_name=f"attendance_records{year_label}.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        
    except Exception as e:
        logger.error(f"Attendance export error: {str(e)}", exc_info=True)
        flash("Error exporting attendance. Please try again.", "error")
        return redirect(url_for("main.admin_attendance"))
