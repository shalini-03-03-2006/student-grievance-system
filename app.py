from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, datetime, os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'complete_grievance_system_2026'

# ================= EMAIL CONFIGURATION =================
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME='shalini13032006@gmail.com',   # use your Gmail
    MAIL_PASSWORD='ffvvqpqhhamxwbpv',            # Gmail app password[web:72]
    MAIL_DEFAULT_SENDER='baske14112007@gmail.com'
)
mail = Mail(app)

# ================= LOGIN SETUP =================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'home'


class User(UserMixin):
    def __init__(self, id, role, name, student_id=None):
        self.id = id
        self.role = role
        self.name = name
        self.student_id = student_id


@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('grievance.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, role, name, student_id FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        return User(user_data[0], user_data[1], user_data[2], user_data[3])
    return None

# ================= DATABASE INITIALIZATION =================


def init_db():
    conn = sqlite3.connect('grievance.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        name TEXT,
        role TEXT CHECK(role IN ('student', 'admin')),
        student_id TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS grievances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        category TEXT CHECK(category IN ('academic','administrative','hostel','examination')),
        anonymous INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending' CHECK(status IN ('pending','under-review','resolved','escalated','closed')),
        priority TEXT DEFAULT 'medium',
        submitted_by INTEGER,
        assigned_to TEXT DEFAULT '',
        resolution TEXT,
        submitted_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        resolved_date DATETIME,
        feedback TEXT,
        FOREIGN KEY (submitted_by) REFERENCES users (id)
    )''')

    # Create default admin if not exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    if cursor.fetchone()[0] == 0:
        pwd = generate_password_hash('admin123')
        cursor.execute(
            "INSERT INTO users (email, password, name, role) VALUES (?, ?, 'Admin', 'admin')",
            ('admin@college.edu', pwd)
        )

    conn.commit()
    conn.close()


init_db()

# ================= EMAIL FUNCTION =================


def send_email(recipient, subject, body):
    try:
        msg = Message(
            subject=subject,
            recipients=[recipient],
            html=body,
            sender=app.config['MAIL_USERNAME']
        )
        mail.send(msg)
        print("Email sent to:", recipient)
        return True
    except Exception as e:
        print("EMAIL ERROR:", e)
        return False

# ================= ROUTES =================


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/student-login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('grievance.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email=? AND role="student"', (email,))
        user_data = cursor.fetchone()
        conn.close()

        if user_data and check_password_hash(user_data[2], password):
            user = User(user_data[0], 'student', user_data[3], user_data[5])
            login_user(user)
            return redirect(url_for('student_dashboard'))

        flash('Invalid student credentials', 'error')

    return render_template('student_login.html')


@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('grievance.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email=? AND role="admin"', (email,))
        user_data = cursor.fetchone()
        conn.close()

        if user_data and check_password_hash(user_data[2], password):
            user = User(user_data[0], 'admin', user_data[3])
            login_user(user)
            return redirect(url_for('admin_dashboard'))

        flash('Invalid admin credentials', 'error')

    return render_template('admin_login.html')


@app.route('/student-register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        student_id = request.form['student_id']
        password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect('grievance.db')
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name,email,password,student_id,role) VALUES (?,?,?,?, 'student')",
                (name, email, password, student_id)
            )
            conn.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('student_login'))
        except sqlite3.IntegrityError:
            flash('Email already registered', 'error')
        finally:
            conn.close()

    return render_template('student_register.html')


@app.route('/student-dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('admin_dashboard'))

    conn = sqlite3.connect('grievance.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM grievances WHERE submitted_by=? ORDER BY submitted_date DESC", (current_user.id,))
    grievances = cursor.fetchall()
    conn.close()

    return render_template('student_dashboard.html', grievances=grievances)


@app.route('/admin-dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))

    conn = sqlite3.connect('grievance.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM grievances ORDER BY submitted_date DESC")
    grievances = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM grievances WHERE status='pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM grievances WHERE status IN ('pending','under-review')")
    unresolved = cursor.fetchone()[0]

    conn.close()

    return render_template('admin_dashboard.html', grievances=grievances, pending=pending, unresolved=unresolved)


@app.route('/submit-grievance', methods=['GET', 'POST'])
@login_required
def submit_grievance():
    if current_user.role != 'student':
        flash('Students only!', 'error')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        priority = request.form['priority']
        description = request.form['description']
        anonymous = 1 if 'anonymous' in request.form else 0

        conn = sqlite3.connect('grievance.db')
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO grievances
               (title, description, category, anonymous, priority, submitted_by)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (title, description, category, anonymous, priority, current_user.id)
        )
        conn.commit()
        grievance_id = cursor.lastrowid

        # Get student details
        cursor.execute('SELECT email, name FROM users WHERE id = ?', (current_user.id,))
        student = cursor.fetchone()
        student_email, student_name = student[0], student[1]
        conn.close()

        # 1. Email confirmation to student
        student_body = f"""
<h2>Grievance #{grievance_id} Submitted Successfully</h2>
<p>Dear {student_name},</p>
<p>Your grievance has been submitted successfully.</p>
<ul>
  <li><strong>ID:</strong> {grievance_id}</li>
  <li><strong>Title:</strong> {title}</li>
  <li><strong>Category:</strong> {category}</li>
  <li><strong>Priority:</strong> {priority}</li>
  <li><strong>Status:</strong> Pending</li>
</ul>
<p><a href="http://localhost:5000/student-dashboard">Track status here</a></p>
<p>Grievance Team</p>
"""
        send_email(student_email, f'Grievance #{grievance_id} Submitted', student_body)

        # 2. Notify all admins
        conn = sqlite3.connect('grievance.db')
        cursor = conn.cursor()
        cursor.execute('SELECT email, name FROM users WHERE role = "admin"')
        admins = cursor.fetchall()
        conn.close()

        student_info = f"{student_name} ({student_email})" if not anonymous else "Anonymous"
        for admin_email, admin_name in admins:
            admin_body = f"""
<h2>New Grievance #{grievance_id} - {title}</h2>
<p>New grievance received from {student_info}:</p>
<ul>
  <li><strong>ID:</strong> {grievance_id}</li>
  <li><strong>Title:</strong> {title}</li>
  <li><strong>Category:</strong> {category}</li>
  <li><strong>Priority:</strong> {priority}</li>
</ul>
<p><a href="http://localhost:5000/grievance/{grievance_id}">View Grievance</a></p>
<p>Grievance Team</p>
"""
            send_email(admin_email, f'New Grievance #{grievance_id}', admin_body)

        flash(f'Grievance #{grievance_id} submitted! Check your email.', 'success')
        return redirect(url_for('student_dashboard'))

    return render_template('submit_grievance.html')


@app.route('/update-grievance/<int:id>', methods=['POST'])
@login_required
def update_grievance(id):
    if current_user.role != 'admin':
        return redirect(url_for('student_dashboard'))

    new_status = request.form['status']
    resolution = request.form.get('resolution', '')
    resolved_date = datetime.datetime.now() if new_status in ['resolved', 'closed'] else None

    conn = sqlite3.connect('grievance.db')
    cursor = conn.cursor()

    # Grievance details
    cursor.execute('SELECT title, anonymous, submitted_by FROM grievances WHERE id = ?', (id,))
    grievance = cursor.fetchone()
    if not grievance:
        conn.close()
        flash('Grievance not found', 'error')
        return redirect(url_for('admin_dashboard'))

    title, anonymous, student_id = grievance

    # Student details
    cursor.execute('SELECT email, name FROM users WHERE id = ?', (student_id,))
    student = cursor.fetchone()

    # Update grievance in DB
    cursor.execute(
        '''UPDATE grievances
           SET status = ?, resolution = ?, resolved_date = ?
           WHERE id = ?''',
        (new_status, resolution, resolved_date, id)
    )
    conn.commit()

    status_names = {
        'pending': 'Pending',
        'under-review': 'Under Review',
        'resolved': 'Resolved',
        'escalated': 'Escalated',
        'closed': 'Closed'
    }

    # === RESOLVED/CLOSED EMAIL NOTIFICATION ===
    if student and not anonymous and new_status in ['resolved', 'closed']:
        student_email, student_name = student
        student_body = f"""
<h2>Grievance #{id} Resolved</h2>
<p>Dear {student_name},</p>
<p>Your grievance "<strong>{title}</strong>" has been
<strong>{status_names[new_status]}</strong>.</p>
{f'<p><strong>Resolution details:</strong> {resolution}</p>' if resolution else ''}
<p>You can view the full details here:
   <a href="http://localhost:5000/grievance/{id}">View Grievance</a></p>
<p>You can also share your feedback here:
   <a href="http://localhost:5000/grievance/{id}/feedback">Give Feedback</a></p>
<p>Thank you for using the Grievance Portal.</p>
<p>Grievance Team</p>
"""
        send_email(
            student_email,
            f"Grievance #{id} {status_names[new_status]}",
            student_body
        )

    conn.close()
    flash('Grievance updated and student notified!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/grievance/<int:id>')
@login_required
def view_grievance(id):
    conn = sqlite3.connect('grievance.db')
    cursor = conn.cursor()
    if current_user.role == 'student':
        cursor.execute("SELECT * FROM grievances WHERE id = ? AND submitted_by = ?", (id, current_user.id))
    else:
        cursor.execute("SELECT * FROM grievances WHERE id = ?", (id,))
    grievance = cursor.fetchone()
    conn.close()
    if not grievance:
        flash('Not found', 'error')
        return redirect(url_for('student_dashboard'))

    grievance_list = list(grievance)
    if grievance_list[10]:  # submitted_date
        grievance_list[10] = grievance_list[10][:10]
    if grievance_list[11]:  # resolved_date
        grievance_list[11] = grievance_list[11][:10]

    return render_template('view_grievance.html', grievance=grievance_list)


@app.route('/grievance/<int:id>/feedback', methods=['GET', 'POST'])
@login_required
def grievance_feedback(id):
    if current_user.role != 'student':
        flash('Only students can give feedback.', 'error')
        return redirect(url_for('home'))

    conn = sqlite3.connect('grievance.db')
    cursor = conn.cursor()

    # Load grievance and ensure it belongs to current student
    cursor.execute(
        "SELECT id, title, status, feedback, submitted_by FROM grievances WHERE id = ?",
        (id,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        flash('Grievance not found.', 'error')
        return redirect(url_for('student_dashboard'))

    gr_id, title, status, existing_feedback, submitted_by = row
    if submitted_by != current_user.id:
        conn.close()
        flash('You are not allowed to give feedback for this grievance.', 'error')
        return redirect(url_for('student_dashboard'))

    if status not in ['resolved', 'closed']:
        conn.close()
        flash('Feedback is allowed only after grievance is resolved or closed.', 'error')
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        feedback_text = request.form.get('feedback', '').strip()

        # 1. Save feedback in DB
        cursor.execute(
            "UPDATE grievances SET feedback = ? WHERE id = ?",
            (feedback_text, id)
        )
        conn.commit()

        # 2. Get student details (for email content)
        cursor.execute("SELECT name, email FROM users WHERE id = ?", (current_user.id,))
        student_row = cursor.fetchone()
        student_name, student_email = student_row if student_row else ("Student", "")

        # 3. Get all admins to notify
        cursor.execute('SELECT name, email FROM users WHERE role = "admin"')
        admins = cursor.fetchall()
        conn.close()

        # 4. Send email to each admin with feedback
        admin_subject = f"Feedback for Grievance #{id} - {title}"
        for admin_name, admin_email in admins:
            admin_body = f"""
<h2>New Feedback for Grievance #{id}</h2>
<p>Dear {admin_name},</p>
<p>The student <strong>{student_name}</strong> ({student_email}) has submitted feedback for the grievance:</p>
<ul>
  <li><strong>ID:</strong> {id}</li>
  <li><strong>Title:</strong> {title}</li>
  <li><strong>Status:</strong> {status.capitalize()}</li>
</ul>
<p><strong>Feedback:</strong></p>
<p>{feedback_text or 'No feedback text provided.'}</p>
<p>You can view the grievance details here:
   <a href="http://localhost:5000/grievance/{id}">View Grievance</a></p>
<p>Grievance Portal</p>
"""
            send_email(admin_email, admin_subject, admin_body)

        # 5. Optional: Thank‑you email to student
        if student_email:
            student_subject = f"Thank you for your feedback on Grievance #{id}"
            student_body = f"""
<h2>Thank You for Your Feedback</h2>
<p>Dear {student_name},</p>
<p>Thank you for sharing your feedback for the grievance
   "<strong>{title}</strong>".</p>
<p>Your comments help us improve the grievance redressal system.</p>
<p>You can view the grievance anytime here:
   <a href="http://localhost:5000/grievance/{id}">View Grievance</a></p>
<p>Grievance Portal</p>
"""
            send_email(student_email, student_subject, student_body)

        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('student_dashboard'))

    # GET request: show form
    conn.close()
    return render_template(
        'grievance_feedback.html',
        grievance_id=gr_id,
        title=title,
        status=status,
        feedback=existing_feedback
    )


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
