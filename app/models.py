from app import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Junction bridge linking both users and students with their administrative checkboxes
user_permissions = db.Table(
    'user_permissions',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True),
    db.Column('student_id', db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=False)
)

class Permission(db.Model):
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)

    # Add these relationships to link back to your users and students
    users = db.relationship('User', secondary=user_permissions, back_populates='permissions', overlaps="students")
    students = db.relationship('Student', secondary=user_permissions, back_populates='permissions', overlaps="users")

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="faculty")
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # Change your existing relationship to this:
    permissions = db.relationship('Permission', secondary=user_permissions, back_populates='users')
    
    @property
    def is_admin(self):
        return self.role == 'admin'

    def get_id(self):
        return f"admin_{self.id}"

    def has_permission(self, permission_name):
        if self.role == 'admin':
            return True
        return any(p.name == permission_name for p in self.permissions)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(UserMixin, db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(150), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    student_number = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    year_section = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="student")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    enrollment_year = db.Column(db.String(4), nullable=True) # Add this

    records = db.relationship('StudentRecord', backref='student_owner', lazy=True, cascade="all, delete-orphan")
    attendance_logs = db.relationship('Attendance', backref='student_owner', lazy=True, cascade="all, delete-orphan")

    # Change your existing relationship to this:
    permissions = db.relationship('Permission', secondary=user_permissions, overlaps="students")

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
    
    # Core Data
    name = db.Column(db.String(150), nullable=True)
    course = db.Column(db.String(100), nullable=True)
    year_section = db.Column(db.String(50), nullable=True)
    company_name = db.Column(db.String(150), nullable=False)
    business_nature = db.Column(db.String(255), nullable=True)
    validity = db.Column(db.String(100), nullable=True)
    notarized_date = db.Column(db.Date, nullable=True)
    expiration_date = db.Column(db.Date, nullable=True)
    
    # Checkboxes
    status = db.Column(db.String(50), nullable=True)
    has_resume = db.Column(db.Boolean, default=False)
    has_medical_cert = db.Column(db.Boolean, default=False)
    has_consent_form = db.Column(db.Boolean, default=False)
    has_moa = db.Column(db.Boolean, default=False)
    has_insurance = db.Column(db.Boolean, default=False)
    has_intent_letter = db.Column(db.Boolean, default=False)
    has_endorsement_letter = db.Column(db.Boolean, default=False)
    
    # Status Tracking
    is_complete = db.Column(db.Boolean, default=False)
    comments = db.Column(db.Text, nullable=True)
    attachments = db.Column(db.String(255), nullable=True)
    student_count = db.Column(db.Integer, nullable=True)
    progress = db.Column(db.Integer, default=0, nullable=True)
    
    # Metadata
    hours_required = db.Column(db.Integer, default=486)
    hours_rendered = db.Column(db.Integer, default=0)
    
    def calculate_progress(self):
        fields = [
            self.has_resume, self.has_medical_cert, self.has_consent_form, 
            self.has_moa, self.has_insurance, self.has_intent_letter, 
            self.has_endorsement_letter
        ]
        completed = sum(1 for field in fields if field is True)
        return int((completed / 7) * 100)
    
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
    
    @property
    def has_all_requirements(self):
        # Returns True if all required fields are checked
        return all([
            self.has_resume, self.has_medical_cert, self.has_consent_form, 
            self.has_moa, self.has_insurance, self.has_intent_letter, 
            self.has_endorsement_letter
        ])

    @property
    def attachment_items(self):
        # Parses the JSON string into a Python list
        import json
        try:
            return json.loads(self.attachments) if self.attachments else []
        except:
            return []

class Attendance(db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    student_name = db.Column(db.String(150), nullable=False)
    student_section = db.Column(db.String(50), nullable=False)
    attendance_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    attendance_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Present")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)