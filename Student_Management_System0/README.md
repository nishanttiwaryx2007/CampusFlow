# CampusFlow — Student Management System

A modern Flask student-management mini-project with IBM Cloudant as its cloud database.

## Features
- Responsive dashboard and course distribution chart
- First-run administrator setup and secure password hashing
- Add, search, edit and delete student records
- Attendance and grade management
- Cloudant document storage

## Setup on Windows / VS Code
1. Install Python 3.10+.
2. Create an IBM Cloud account at https://cloud.ibm.com/ and provision an IBM Cloudant service.
3. Create an IAM service credential. Copy its service URL and API key.
4. Copy `.env.example` to `.env` and fill in `CLOUDANT_URL` and `CLOUDANT_APIKEY`. Keep `.env private.
5. Open PowerShell in this folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py app.py
```

If PowerShell blocks activation, use:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

6. Visit http://127.0.0.1:5000/setup and create the first administrator.
7. Sign in at http://127.0.0.1:5000.

The app automatically creates the `student_management` Cloudant database if it does not exist.

## Student document example
```json
{
  "type": "student",
  "name": "Aarav Sharma",
  "roll": "CSE001",
  "course": "Computer Science",
  "email": "aarav@example.com",
  "phone": "9876543210",
  "grade": "A",
  "attendance": 92
}
```

## Demo suggestion
Add a few sample students, search by roll/name, update attendance and grades, and show the dashboard chart changing.

## Security notes
Never share `.env` or expose your API key. This is an educational starter, not a production SIS. For deployment add CSRF protection, rate limiting, stricter role permissions, audit logs, backups, HTTPS and privacy controls.
