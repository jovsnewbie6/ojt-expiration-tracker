# Attendance Feature - User Guide

## Overview
A simple and efficient attendance tracking system for students and administrators. Students submit daily attendance, and admins can view, filter, and export records.

---

## Student Portal - Attendance Section

### How Students Submit Attendance

1. **Navigate to Attendance**
   - Click "📋 Attendance" in the left sidebar of the student portal
   - Or go to `/student/attendance`

2. **Fill Out Attendance Form**
   - **Student Name**: Auto-filled from your account
   - **Section**: Auto-filled from your year/section
   - **Date**: Select the attendance date using date picker
   - **Time**: Enter time in HH:MM format (e.g., 09:00)
   - **Status**: Choose "✓ Present" or "✗ Absent"

3. **Submit**
   - Click "Submit Attendance"
   - See message: "✓ Attendance submitted successfully"

4. **Download Records**
   - Click "📥 Download My Attendance" button
   - Excel file downloads with all your attendance records
   - Includes: Student Name, Date, Time, Status

### Data Collected
- Student Name (automatic)
- Section (automatic)
- Attendance Date
- Attendance Time
- Status (Present/Absent)
- Submission Timestamp

---

## Admin Portal - Attendance Management

### How Admins View Attendance

1. **Navigate to Attendance**
   - Click "📋 Attendance" in the admin left sidebar
   - Or go to `/admin/attendance`

2. **View Attendance Records**
   - See table with all student attendance records
   - Columns: Student Name | Section | Date | Time | Status
   - Status shows as colored badge:
     - 🟢 Green = Present
     - 🔴 Red = Absent

3. **Filter by Year**
   - Use dropdown at top: "Filter by Year"
   - Select year to view only that year's records
   - Select "All Years" to see everything

4. **Export to Excel**
   - Click "📥 Export Excel" button
   - Downloads compiled Excel file with selected year's data
   - Filename: `attendance_records.xlsx` or `attendance_records_2026.xlsx` if year filtered
   - Includes: Student Name, Date, Time, Status, Section

### Admin Features
- View all student attendance in one table
- Filter by year quickly
- Export to Excel for reports
- One-click compilation of attendance data
- Search functionality for specific dates/students

---

## Data Structure

### Attendance Table (Database)
```
- id: Primary key
- student_id: Link to student
- student_name: Student's full name
- student_section: Student's year/section
- attendance_date: Date of attendance
- attendance_time: Time in HH:MM format
- status: "Present" or "Absent"
- created_at: When record was created
```

---

## URL Endpoints

### Student Routes
- `GET /student/attendance` - View attendance form
- `POST /student/attendance` - Submit attendance
- `GET /student/attendance/export` - Download student's attendance as Excel

### Admin Routes
- `GET /admin/attendance` - View all attendance records
- `GET /admin/attendance?year=2026` - Filter by year
- `GET /admin/attendance/export` - Export all attendance to Excel
- `GET /admin/attendance/export?year=2026` - Export specific year to Excel

---

## Technical Details

### Simple Design
- Minimal code to avoid errors
- Direct database operations
- No complex calculations
- Standard Excel export using pandas

### Error Handling
- User-friendly error messages
- Database connection verified before operations
- Invalid data rejected with clear messages

### Performance
- Efficient database queries
- Indexed by student_id and attendance_date
- Fast Excel generation with pandas

---

## Feature Summary

✓ Students submit attendance with date/time/status  
✓ Student names and sections auto-filled  
✓ Admin views compiled attendance table  
✓ Year filter for easy navigation  
✓ Export to Excel for both students and admins  
✓ Simple, clean interface matching MOA portal design  
✓ No complex validations or calculations  
✓ Ready for production use  

---

## Testing Checklist

✓ Student can submit attendance  
✓ Attendance saved to database  
✓ Admin can view all attendance records  
✓ Year filter works correctly  
✓ Excel export downloads with correct data  
✓ Auto-filled fields show correct values  
✓ Status badges display correctly  

---

## Deployment Notes

- Database migration: attendance table created automatically
- No additional dependencies (pandas already installed)
- Works with both SQLite (dev) and PostgreSQL (production)
- Compatible with existing authentication system
- Integrates seamlessly with MOA portal

**Status**: ✅ Production Ready
