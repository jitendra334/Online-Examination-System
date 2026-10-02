# Online Examination System 🎓

![Django](https://img.shields.io/badge/Django-5.2+-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Bootstrap 5](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)
![Chart.js](https://img.shields.io/badge/Chart.js-4.4-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white)

A comprehensive, production-ready, full-stack **Online Examination & Assessment Management System** built with **Python 3, Django, PostgreSQL, Bootstrap 5, and Chart.js**. Engineered specifically as a benchmark **BTech Computer Science & Engineering capstone and campus placement portfolio project**.

---

## 🌟 Key System Highlights

* **3 Distinct Role Portals:** Dedicated custom dashboards and security access controls for **Administrators**, **Faculty/Examiners**, and **Students**.
* **Interactive Examination Hall Interface:**
  * Real-time countdown timer with auto-submit on timeout.
  * Interactive **Question Palette** with color-coded live statuses (*Answered*, *Unanswered*, *Marked for Review*, *Answered & Marked*).
  * **Asynchronous AJAX Auto-Save** on option selection (zero page refreshes).
  * Shuffle question order and option order for academic integrity.
  * Negative marking deduction support (customizable per exam/question).
* **Comprehensive Analytics & Result Generation:**
  * Automated server-side score calculation, accuracy percentages, pass/fail status, and batch rankings.
  * Detailed Question-by-Question Solution Review with verified explanations.
  * **Downloadable Official PDF Scorecards & Certificates** generated dynamically via ReportLab.
  * **Interactive Chart.js Visualizations**: Score progression timeline, accuracy distribution donut, pass/fail ratios, and subject coverage bars.
* **Merit Leaderboard & CSV Marks Roster Export**: Batch-wide and global student ranking tables with 1-click CSV marksheet export for instructors.
* **Enterprise Security**: Django PBKDF2 password hashing, CSRF token validation on all AJAX calls, server-side timer validation, and custom role decorators (`@admin_required`, `@teacher_required`, `@student_required`).

---

## 👥 User Roles & Permissions

### 1. 🛡️ Administrator
* Full administrative control over students, teachers, subjects, and exams.
* Deactivate/activate user accounts and manage permissions.
* Real-time overview of system-wide metrics, pass rates, and exam participation charts.
* Complete database access via custom admin console and Django Admin.

### 2. 👨‍🏫 Teacher / Examiner
* Create, configure, publish, and manage MCQ tests.
* Add/edit/delete questions with 4 options and verified explanations.
* Bulk import questions via **CSV / JSON** files.
* Configure negative marking penalties, duration limits, passing marks, and question shuffling.
* Inspect student attempts, review accuracy breakdown, and export student results to **CSV**.

### 3. 🎓 Student
* Browse active published examinations by subject.
* Read instructions and rules before starting.
* Live MCQ examination room with countdown timer, question palette, review tags, and clear response.
* View instant scorecard and question explanations upon completion.
* Track score progression trends and download verified PDF certificates.
* Compete on university-wide and exam-specific leaderboards.

---

## 🏗️ Project Architecture & App Structure

```text
Online Examination System/
│
├── accounts/               # Custom User model, Role decorators, Auth forms & views
│   ├── management/commands/seed_data.py   # One-click demo data seeder
│   ├── models.py           # User model with ADMIN, TEACHER, STUDENT roles
│   ├── forms.py            # Student & Teacher registration, profile forms
│   ├── decorators.py       # @admin_required, @teacher_required, @student_required
│   └── views.py            # Login, register, profile, user management views
│
├── exams/                  # Subject and Exam configuration
│   ├── models.py           # Subject & Exam models with timing & scoring logic
│   ├── forms.py            # SubjectForm, ExamForm
│   └── views.py            # Exam CRUD, toggle publish, instructions view
│
├── questions/              # Question bank and option management
│   ├── models.py           # Question & Option models
│   ├── forms.py            # QuestionWith4OptionsForm, BulkUploadForm
│   └── views.py            # Question CRUD, CSV/JSON bulk import
│
├── results/                # Exam attempts, AJAX saving, PDF generation, rankings
│   ├── models.py           # ExamAttempt & StudentAnswer models
│   ├── views.py            # Exam hall UI, AJAX auto-save, PDF generation, leaderboards
│   └── urls.py             # Examination & results endpoints
│
├── dashboard/              # Role-specific analytics & Chart.js dashboards
│   └── views.py            # Admin, Teacher, and Student dashboard controllers
│
├── templates/              # Reusable modern Bootstrap 5 UI templates
│   ├── base.html, navbar.html, sidebar.html, footer.html
│   ├── accounts/           # Login, registration, profile, user admin
│   ├── dashboard/          # Admin, Teacher, Student dashboards
│   ├── exams/              # Exam lists, forms, instruction hall
│   ├── questions/          # Question list, form, bulk upload
│   └── results/            # Take exam hall, result scorecard, leaderboard
│
├── static/                 # Stylesheets, JavaScript, assets
│   ├── css/style.css       # Custom themes, question palette styles, timer alerts
│   └── js/main.js          # UI utilities and tooltips
│
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚡ Quick Start & Installation

### Prerequisites
* **Python 3.10+** (Tested on Python 3.12)
* **pip** package manager
* **PostgreSQL** (Optional for production; SQLite is used by default for zero-friction local setup)

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/yourusername/online-examination-system.git
cd "Online Examination System"

# Create and activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Optional: If connecting to PostgreSQL, specify `DATABASE_URL=postgres://user:password@localhost:5432/exam_db` inside `.env`)*

### 4. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Seed Demo Data (Instant Placement Interview Demo)
Run the built-in database seeder to immediately populate realistic users, subjects, exams, questions, and evaluated test attempts:
```bash
python manage.py seed_data
```

### 6. Start the Local Server
```bash
python manage.py runserver
```
Visit **`http://127.0.0.1:8000/`** in your browser.

---

## 🔑 Pre-Configured Demo Credentials

| Role | Username | Password | Email |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin123` | admin@examportal.edu |
| **Faculty (Teacher)** | `prof_sharma` | `teacher123` | r.sharma@examportal.edu |
| **Faculty (Teacher)** | `dr_anita` | `teacher123` | anita.verma@examportal.edu |
| **Student 1** | `rahul_cse` | `student123` | rahul.cse@examportal.edu |
| **Student 2** | `priya_it` | `student123` | priya.it@examportal.edu |
| **Student 3** | `amit_kumar` | `student123` | amit.kumar@examportal.edu |

> **Tip for Interviews:** The login page features **1-Click Quick Demo Login** buttons for Administrator, Faculty, and Student roles for instant switching.

---

## 🚀 Cloud Deployment (Render / Railway)

### Deploying to Render
1. Push this repository to GitHub.
2. Create a new **Web Service** on [Render](https://render.com).
3. Connect your GitHub repository.
4. Set Build Command:
   ```bash
   pip install -r requirements.txt && python manage.py migrate && python manage.py seed_data
   ```
5. Set Start Command:
   ```bash
   gunicorn exam_project.wsgi:application
   ```
6. Add Environment Variables:
   * `SECRET_KEY`: `your-secure-key`
   * `DEBUG`: `False`
   * `DATABASE_URL`: Add a Render PostgreSQL database connection string.

---

## 📊 Database Schema Highlights

* **User**: Extended `AbstractUser` with role differentiation (`ADMIN`, `TEACHER`, `STUDENT`), `student_id`, `employee_id`, and `department`.
* **Subject**: Academic courses with codes (`CS301`), icons, and visual color codes.
* **Exam**: Duration, total & passing marks, negative marking flags, question shuffling rules, and publish status.
* **Question & Option**: MCQ statement, marks, negative penalty override, explanation, and 4 option records with `is_correct` flags.
* **ExamAttempt**: Stores candidate attempt, start/end timestamps, server remaining time, serialized question order, final calculated scores, accuracy %, and pass/fail outcome.
* **StudentAnswer**: Individual question selection, correctness flag, marks awarded, and review status.

---

## 👨‍💻 Author & Placement Portfolio

* **Project:** Online Examination & Assessment System
* **Domain:** Full-Stack Web Development, Educational Technology & Distributed Systems
* **Technologies:** Python, Django 5, PostgreSQL, Bootstrap 5, Chart.js, ReportLab PDF, REST/AJAX

---
*Developed with modern software engineering best practices.*
