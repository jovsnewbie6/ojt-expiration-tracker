from app import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Junction bridge linking non-student users with their administrative checkboxes
user_permissions = db.Table(
    'user_permissions',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)
)

class Permission(db.Model):
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="faculty") # admin, faculty, coordinator
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # Permissions dynamic tracking mapping
    permissions = db.relationship('Permission', secondary=user_permissions, lazy='subquery',
                                  backref=db.backref('users', lazy=True))
    
    @property
    def is_admin(self):
        return self.role == 'admin'

    def get_id(self):
        return f"admin_{self.id}"

    def has_permission(self, permission_name):
        if self.role == 'admin':
            return True # Master overrides
        return any(p.name == permission_name for p in self.permissions)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(UserMixin, db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # Add the email column here
    email = db.Column(db.String(150), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Required by routes.py for registration and lookups
    student_number = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    
    # Existing fields
    year_section = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="student")
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # Relationships
    records = db.relationship('StudentRecord', backref='student_owner', lazy=True, cascade="all, delete-orphan")
    attendance_logs = db.relationship('Attendance', backref='student_owner', lazy=True, cascade="all, delete-orphan")

    def get_id(self):
        return f"student_{self.id}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class StudentRecord(db.Model):
    __tablename__ = "student_records"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    course = db.Column(db.String(100), nullable=True)
    business_nature = db.Column(db.String(255), nullable=True)
    validity = db.Column(db.String(100), nullable=True)
    company_name = db.Column(db.String(150), nullable=False)
    has_resume = db.Column(db.Boolean, default=False)
    has_moa = db.Column(db.Boolean, default=False)
    has_medical_cert = db.Column(db.Boolean, default=False)
    expiration_date = db.Column(db.Date, nullable=True)
    hours_required = db.Column(db.Integer, default=486)
    hours_rendered = db.Column(db.Integer, default=0)
    
    # Matching the routes.py and database columns
    name = db.Column(db.String(150), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    year_section = db.Column(db.String(50), nullable=True)
    
    @property
    def year_only(self):
        return self.year_section.split('-')[0] if self.year_section and '-' in self.year_section else "N/A"

    @property
    def section_only(self):
        return self.year_section.split('-')[1] if self.year_section and '-' in self.year_section else "N/A"

    @property
    def days_left(self):
        if self.expiration_date:
            delta = self.expiration_date - datetime.utcnow().date()
            return max(0, delta.days)
        return 0

class Attendance(db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    student_name = db.Column(db.String(150), nullable=False)
    student_section = db.Column(db.String(50), nullable=False)
    attendance_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    attendance_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Present") # Present, Absent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)