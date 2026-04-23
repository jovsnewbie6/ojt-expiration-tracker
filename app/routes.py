import csv
import io
import json
import os
import uuid
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
from app.models import StudentRecord, User, Student

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


def parse_integer(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def allowed_file(filename):
    if not filename:
        return False
    allowed_extensions = {"pdf", "jpg", "jpeg", "png", "doc", "docx", "xls", "xlsx", "txt"}
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
        if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
            abort(403)
        return view(*args, **kwargs)

    return wrapped


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
                )
                db.session.add(record)
                db.session.commit()

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
    )


@main_bp.route("/student/register", methods=["GET", "POST"])
def student_register():
    if current_user.is_authenticated:
        return redirect(url_for("main.student_portal"))

    if request.method == "POST":
        student_number = request.form.get("student_number", "").strip()
        full_name = request.form.get("full_name", "").strip()
        year_section = request.form.get("year_section", "").strip()
        password = request.form.get("password", "").strip()

        if not student_number or not full_name or not year_section or not password:
            flash("Please complete all registration fields.", "error")
            return render_template("register.html")

        if Student.query.filter_by(student_number=student_number).first():
            flash("That student number is already registered.", "error")
            return render_template("register.html")

        student = Student(
            student_number=student_number,
            name=full_name,
            year_section=year_section,
            email=None,
        )
        student.set_password(password)
        db.session.add(student)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("main.student_login"))

    return render_template("register.html")


@main_bp.route("/admin/create-staff", methods=["GET", "POST"])
@login_required
@admin_required
def admin_create_staff():
    if not current_user.is_admin:
        abort(403)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Please provide both a username and password.", "error")
            return render_template("add_admin.html")

        if User.query.filter_by(username=username).first():
            flash("That admin username is already taken.", "error")
            return render_template("add_admin.html")

        admin = User(username=username, role="admin")
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()

        flash("New admin user created successfully.", "success")
        return redirect(url_for("main.admin_dashboard"))

    return render_template("add_admin.html")


@main_bp.route("/student/login", methods=["GET", "POST"])
def student_login():
    if current_user.is_authenticated:
        return redirect(url_for("main.student_portal"))

    if request.method == "POST":
        student_number = request.form.get("student_number", "").strip()
        password = request.form.get("password", "").strip()
        student = Student.query.filter_by(student_number=student_number).first()

        if student and student.check_password(password):
            login_user(student)
            flash("Student login successful.", "success")
            return redirect(url_for("main.student_portal"))

        flash("Invalid student credentials.", "error")

    return render_template("student_login.html")


@main_bp.route("/student/logout")
@login_required
def student_logout():
    if isinstance(current_user, Student):
        logout_user()
        flash("Student signed out.", "success")
        return redirect(url_for("main.student_login"))
    return redirect(url_for("main.admin_dashboard"))


@main_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for("main.admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        admin = User.query.filter_by(username=username, role="admin").first()

        if admin and admin.check_password(password):
            login_user(admin)
            flash("Admin signed in successfully.", "success")
            return redirect(url_for("main.admin_dashboard"))

        flash("Invalid admin credentials.", "error")

    return render_template(
        "admin_login.html",
        is_admin=current_user.is_authenticated,
    )


@main_bp.route("/admin/logout")
@login_required
@admin_required
def admin_logout():
    logout_user()
    flash("Admin signed out.", "success")
    return redirect(url_for("main.admin_login"))


@main_bp.route("/admin/dashboard")
@login_required
@admin_required
def admin_dashboard():
    search_term = request.args.get("search", "").strip()
    records_query = StudentRecord.query.order_by(StudentRecord.expiration_date)

    if search_term:
        records_query = records_query.filter(func.lower(StudentRecord.name).contains(search_term.lower()))

    records = records_query.all()
    totals = {
        "pending": StudentRecord.query.filter_by(status="Pending").count(),
        "incomplete": StudentRecord.query.filter_by(status="Incomplete").count(),
        "approved": StudentRecord.query.filter_by(status="Approved").count(),
    }
    return render_template(
        "admin_dashboard.html",
        records=records,
        totals=totals,
        requirement_fields=REQUIREMENT_FIELDS,
        search_term=search_term,
        is_admin=current_user.is_authenticated,
    )


@main_bp.route("/admin/edit/<int:record_id>", methods=["GET", "POST"])
@login_required
@admin_required
def admin_edit(record_id):
    record = StudentRecord.query.get_or_404(record_id)

    if request.method == "POST":
        record.name = request.form.get("name", record.name).strip()
        record.year_section = request.form.get("year_section", record.year_section).strip()
        record.company_name = request.form.get("company_name", record.company_name).strip()
        record.business_nature = request.form.get("business_nature", record.business_nature).strip()
        record.validity = request.form.get("validity", record.validity).strip()
        record.status = request.form.get("status", record.status)
        record.has_resume = bool(request.form.get("has_resume"))
        record.has_med_cert = bool(request.form.get("has_med_cert"))
        record.has_consent_form = bool(request.form.get("has_consent_form"))
        record.has_moa = bool(request.form.get("has_moa"))
        record.has_insurance = bool(request.form.get("has_insurance"))
        record.has_intent_letter = bool(request.form.get("has_intent_letter"))
        record.has_endorsement_letter = bool(request.form.get("has_endorsement_letter"))

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
@admin_required
def admin_delete(record_id):
    record = StudentRecord.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    flash("Submission removed successfully.", "success")
    return redirect(url_for("main.admin_dashboard"))


@main_bp.route("/admin/download-report")
@login_required
@admin_required
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
@admin_required
def export_approved():
    approved_records = StudentRecord.query.filter_by(status="Approved").order_by(StudentRecord.expiration_date).all()

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
