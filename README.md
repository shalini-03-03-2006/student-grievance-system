1. Project Overview
This project is a Student Grievance Redressal System built as a Flask web application to help students submit complaints online and track their status while enabling administrators to manage, resolve, and close grievances transparently.

Key goals:

Provide a centralized platform for students to submit grievances.

Ensure transparent tracking of status (pending, under review, resolved, escalated, closed).

Enable admins to view, update, and resolve complaints through an admin dashboard.

Send email notifications at important stages (submission, resolution, feedback).

2. Technologies Used
Frontend: HTML, CSS, Bootstrap (for responsive UI and forms).

Backend: Python, Flask, Flask‑Login, Flask‑Mail.

Database: SQLite (grievance.db).

Security: Password hashing using werkzeug.security.

Environment management: python-dotenv for loading credentials from .env.
These match common tech stacks for grievance systems and Flask apps.

3. System Features (what you implemented)
You can list features like this:

User Authentication and Roles

Student registration and login with hashed passwords.

Default admin user created automatically (e.g., admin@college.edu / admin123).

Role‑based access:

Student: submit grievances, view only their own complaints, give feedback.

Admin: view all grievances, update status, add resolution, see dashboards.

Grievance Submission

Form for students to submit a grievance with:

Title, category (academic/administrative/hostel/examination), description.

Priority (low/medium/high).

Option to submit anonymously (admin sees “Anonymous” instead of name/email).

Data stored in grievances table with timestamps.

Anonymous Submission Logic

Checkbox in form (anonymous), stored as 0/1 in DB.

In admin notification emails and views, if anonymous = 1, the student identity is hidden.

Student still receives email updates on their own email when not anonymous.

Student Dashboard

Shows list of grievances submitted by logged‑in student.

Displays status, category, priority, and dates.

Allows navigation to view full grievance details and give feedback after resolution.

Admin Dashboard

Lists all grievances sorted by latest submission.

Shows counts of:

Pending grievances.

Unresolved (pending + under review).

Admin can:

Change status (pending → under review → resolved/escalated/closed).

Enter resolution text.

See submitted and resolved dates.

Email Notifications (Flask‑Mail)
​

On grievance submission:

Email sent to student with grievance ID, details, and link to track status.

Notification email sent to all admins with grievance info and a link to view it.

On status update to resolved/closed:

Email sent to student with resolution details and links to view grievance and give feedback.

On feedback submission:

Email sent to all admins with the student’s feedback.

Thank‑you email sent to student.

Feedback Module
​

Students can submit feedback for a grievance only after it is resolved or closed.

Ensures:

Only the original student who submitted it can give feedback.

Feedback is stored in grievances.feedback.

Feedback is emailed to administrators to improve service quality.

Status Tracking and Dates

Each grievance has:

submitted_date (automatically set on insert).

resolved_date (set when status becomes resolved/closed).

Templates format dates (e.g., show only date part).

Students can easily see current status and when it was resolved.

4. Database Design (tables you created)
You can describe the schema like this:

Table: users

id (PK, auto increment)

email (unique)

password (hashed)

name

role (student / admin)

student_id (for students)

Table: grievances

id (PK)

title, description

category (academic, administrative, hostel, examination)

anonymous (0/1)

status (pending, under-review, resolved, escalated, closed)

priority (low, medium, high)

submitted_by (FK to users.id)

assigned_to (text, future use for department assignment)

resolution (text)

submitted_date (default current timestamp)

resolved_date (nullable)

feedback (text, nullable)

Mention that DB is initialized automatically by an init_db() function when the app starts.

5. Key Code Modules and Changes You Made
You can explain your main Python modules and important improvements:

Authentication & User Handling

User class using UserMixin from Flask‑Login.

load_user function loads user from users table using user_id.

Student and admin login routes validate credentials and log in with login_user().

Anonymous Grievance Handling

In the submit form, you added a proper Bootstrap checkbox:

xml
<div class="form-check mb-3">
  <input class="form-check-input" type="checkbox" id="anonymous" name="anonymous" value="1">
  <label class="form-check-label" for="anonymous">
    Submit Anonymously
  </label>
</div>
Backend:

python
anonymous = 1 if 'anonymous' in request.form else 0
Admin emails show “Anonymous” when anonymous == 1.

Email Utility Function

Central send_email(recipient, subject, body) function using Flask‑Mail to avoid repeating code.

Handles errors in try/except and logs failures.

Grievance Update and Notification Logic

Admin update route:

Updates status, resolution text, and resolved_date if needed.

Sends resolution email to student (if not anonymous).

Provides a feedback link in the email.

Feedback Route Enhancements

Ensures:

Only the original student can give feedback.

Feedback is accepted only when the grievance is resolved/closed.

Sends notification emails to admins and a thank‑you email to the student after feedback.

Template Improvements

Added Bootstrap classes to forms, tables, and buttons for better UI.

Proper alignment of “Submit Anonymously” checkbox.

Clear messages using Flask flash() for success/error.

6. How to Run the Project (for GitHub README)
Include a section like:

Clone and install:

bash
git clone https://github.com/yourusername/student-grievance-system.git
cd student-grievance-system
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
Set environment variables (optional)

Create a .env file with:

text
MAIL_USERNAME=yourgmail@gmail.com
MAIL_PASSWORD=your_app_password
Run the app:

bash
python app.py
Open http://127.0.0.1:5000.

7. “Changes Made” section for GitHub
Since you already had a basic version, you can add a “What’s New / Improvements” section:

Implemented role‑based login (student/admin) with hashed passwords.

Added anonymous grievance submission with proper checkbox UI and backend logic.

Implemented email notifications:

On submission (student + admins).

On resolution (student).

On feedback (admins + student acknowledgement).

Added feedback module linked to resolved grievances.

Added admin dashboard metrics (pending, unresolved) and better listing.

Improved UI using Bootstrap (forms, cards, alerts).

Structured database initialization with an init_db() function.

You can base wording on how other grievance system reports describe features and phases: planning, analysis, design, implementation, testing.
