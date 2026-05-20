import json
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


# Association table for many-to-many relationship between User and Permission
user_permissions = db.Table(
    "user_permissions",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permissions.id"), primary_key=True),
)

# Association table for many-to-many relationship between Student and Permission
student_permissions = db.Table(
    "student_permissions",
    db.Column("student_id", db.Integer, db.ForeignKey("students.id"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permissions.id"), primary_key=True),
)


class StudentRecord(db.Model):
    __tablename__ = "student_records"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=True)
    name = db.Column(db.String(140), nullable=False)
    course = db.Column(db.String(80), nullable=False)
    year_section = db.Column(db.String(60), nullable=False, default="")
    college_year = db.Column(db.String(30), nullable=True, default="")
    section = db.Column(db.String(50), nullable=True, default="")
    company_name = db.Column(db.String(120), nullable=False, default="")
    business_nature = db.Column(db.String(120), nullable=False, default="")
    validity = db.Column(db.String(60), nullable=False, default="")
    notarized_date = db.Column(db.Date, nullable=True)
    student_count = db.Column(db.Integer, nullable=False, default=0)
    attachments = db.Column(db.Text, nullable=False, default="[]")
    status = db.Column(db.String(30), nullable=False, default="Pending")
    has_resume = db.Column(db.Boolean, nullable=False, default=False)
    has_med_cert = db.Column(db.Boolean, nullable=False, default=False)
    has_consent_form = db.Column(db.Boolean, nullable=False, default=False)
    has_moa = db.Column(db.Boolean, nullable=False, default=False)
    has_insurance = db.Column(db.Boolean, nullable=False, default=False)
    has_intent_letter = db.Column(db.Boolean, nullable=False, default=False)
    has_endorsement_letter = db.Column(db.Boolean, nullable=False, default=False)
    is_complete = db.Column(db.Boolean, nullable=False, default=False)
    expiration_date = db.Column(db.Date, nullable=False)
    comments = db.Column(db.Text, nullable=True, default="")
    progress = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    REQUIREMENT_FIELDS = [
        ("has_resume", "Resume"),
        ("has_med_cert", "Medical Certificate"),
        ("has_consent_form", "Consent Form"),
        ("has_moa", "MOA"),
        ("has_insurance", "Insurance"),
        ("has_intent_letter", "Intent Letter"),
        ("has_endorsement_letter", "Endorsement Letter"),
    ]

    @property
    def expired(self) -> bool:
        return self.expiration_date < datetime.today().date()

    @property
    def days_left(self) -> int:
        return (self.expiration_date - datetime.today().date()).days

    @property
    def missing_requirements(self):
        return [
            label
            for field, label in self.REQUIREMENT_FIELDS
            if not getattr(self, field)
        ]

    @property
    def attachment_items(self):
        try:
            return json.loads(self.attachments or "[]")
        except (TypeError, ValueError):
            return []

    @property
    def has_all_requirements(self):
        return len(self.missing_requirements) == 0

    @property
    def display_year_section(self):
        if self.year_section:
            return self.year_section
        fallback = " ".join(filter(None, [self.college_year, self.section])).strip()
        return fallback or "N/A"

    def calculate_progress(self):
        """Calculate progress percentage based on completed requirements (0-100)"""
        total_requirements = len(self.REQUIREMENT_FIELDS)
        completed = sum(1 for field, _ in self.REQUIREMENT_FIELDS if getattr(self, field))
        return int((completed / total_requirements) * 100) if total_requirements > 0 else 0


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="admin")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    permissions = db.relationship(
        "Permission",
        secondary=user_permissions,
        backref=db.backref("users", lazy="dynamic"),
        lazy="select",
    )

    @property
    def is_admin(self):
        return self.role == "admin"

    def get_id(self):
        return f"admin_{self.id}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Student(UserMixin, db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    student_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(140), nullable=False)
    year_section = db.Column(db.String(60), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    role = db.Column(db.String(30), nullable=False, default="student")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    permissions = db.relationship(
        "Permission",
        secondary=student_permissions,
        backref=db.backref("students", lazy="dynamic"),
        lazy="select",
    )

    @property
    def is_admin(self):
        return False

    def get_id(self):
        return f"student_{self.id}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Permission(db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Permission {self.name}>"

