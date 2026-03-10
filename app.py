from flask import Flask, render_template, request, redirect, session, make_response
import sqlite3
import random
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "hr_analytics_pro_2026"

def get_db():
    conn = sqlite3.connect('hr.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if os.path.exists('hr.db'):
        os.remove('hr.db')
        print("🗑️  Old database deleted")
    
    conn = get_db()
    c = conn.cursor()
    
    # ✅ USERS TABLE (4 columns)
    c.execute('''CREATE TABLE users (
        id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT
    )''')
    
    # ✅ EMPLOYEES TABLE (15 columns EXACTLY)
    c.execute('''CREATE TABLE employees (
        employee_id INTEGER PRIMARY KEY,
        name TEXT, 
        department TEXT, 
        gender TEXT, 
        age INTEGER,
        education_level TEXT, 
        job_role TEXT, 
        monthly_income REAL,
        years_at_company INTEGER, 
        sick_days INTEGER, 
        vacation_days INTEGER,
        performance_score REAL, 
        active INTEGER, 
        status TEXT,
        join_date TEXT
    )''')
    
    c.execute("INSERT INTO users VALUES (1, 'admin', '151124', 'admin')")
    
    # Realistic employee data
    names_male = ['Rahul', 'Amit', 'Vikram', 'Rohan', 'Karan']
    names_female = ['Priya', 'Sneha', 'Neha', 'Divya', 'Pooja']
    depts = ['IT', 'HR', 'Sales', 'Finance', 'Engineering']
    roles = ['Engineer', 'Manager', 'Analyst', 'Specialist']
    
    print("🚀 Creating 250 realistic employees...")
    random.seed(42)
    
    for i in range(1, 251):
        gender = random.choice(['Male', 'Female'])
        names = names_male if gender == 'Male' else names_female
        name = f"{random.choice(names)}_{i:03d}"
        dept = random.choice(depts)
        
        # Dept-specific salary ranges
        salary_ranges = {
            'IT': (65000, 110000), 'Engineering': (70000, 120000),
            'Finance': (60000, 90000), 'HR': (50000, 80000),
            'Sales': (55000, 95000)
        }
        min_sal, max_sal = salary_ranges[dept]
        salary = round(random.uniform(min_sal, max_sal), 2)
        
        # Status distribution
        status_roll = random.random()
        if status_roll < 0.85:
            status, active = 'Active', 1
        elif status_roll < 0.95:
            status, active = 'Inactive', 0
        else:
            status, active = 'On Leave', 0
        
        # ✅ EXACTLY 15 VALUES FOR 15 COLUMNS
        c.execute('''INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (i,                                    # 1. employee_id
                  name,                                # 2. name
                  dept,                                # 3. department
                  gender,                              # 4. gender
                  random.randint(22, 52),              # 5. age
                  random.choice(['Bachelor', 'Master', 'MBA']),  # 6. education_level
                  random.choice(roles),                # 7. job_role
                  salary,                              # 8. monthly_income
                  random.randint(0, 6),                # 9. years_at_company
                  random.randint(0, 12),               # 10. sick_days
                  random.randint(0, 10),               # 11. vacation_days
                  round(random.uniform(3.0, 5.0), 1),  # 12. performance_score
                  active,                              # 13. active
                  status,                              # 14. status
                  datetime.now().strftime('%Y-%m-%d'))) # 15. join_date
    
    conn.commit()
    conn.close()
    print("✅ 250 employees created successfully!")
    print("📊 Database ready for your dashboard!")

init_db()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username=? AND password=?',
                           (request.form['username'], request.form['password'])).fetchone()
        conn.close()
        if user:
            session['user'] = user['username']
            return redirect('/dashboard')
        return render_template('index.html', error='Invalid credentials')
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    
    conn = get_db()
    
    # All data your beautiful dashboard expects
    total = conn.execute('SELECT COUNT(*) FROM employees').fetchone()[0]
    active = conn.execute('SELECT COUNT(*) FROM employees WHERE active=1').fetchone()[0]
    
    # Department data WITH total_salary
    depts = conn.execute('''
        SELECT department, 
               COUNT(*) as count, 
               AVG(monthly_income) as avg_salary,
               SUM(monthly_income) as total_salary
        FROM employees GROUP BY department
    ''').fetchall()
    
    # Gender breakdown
    gender_data = conn.execute('SELECT gender, COUNT(*) as count FROM employees GROUP BY gender').fetchall()
    
    # Leave totals
    sick_leave = conn.execute('SELECT SUM(sick_days) FROM employees').fetchone()[0] or 0
    vacation_leave = conn.execute('SELECT SUM(vacation_days) FROM employees').fetchone()[0] or 0
    
    avg_age = conn.execute('SELECT AVG(age) FROM employees').fetchone()[0] or 0
    avg_salary = conn.execute('SELECT AVG(monthly_income) FROM employees').fetchone()[0] or 0
    
    conn.close()
    
    return render_template('dashboard.html',
                         total=total, active=active,
                         depts=[dict(d) for d in depts],
                         gender_data=[dict(g) for g in gender_data],
                         sick_leave=int(sick_leave), vacation_leave=int(vacation_leave),
                         avg_salary=float(avg_salary), avg_age=int(avg_age))

@app.route('/add_employee.html')
def add_employee_page():
    if 'user' not in session:
        return redirect('/')
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) FROM employees').fetchone()[0]
    conn.close()
    return render_template('add_employee.html', total=total)

@app.route('/add_employee', methods=['POST'])
def add_employee():
    if 'user' not in session:
        return redirect('/')
    # Add your POST handler here
    pass



@app.route('/logout')
def logout():
    session.clear()
    resp = make_response(redirect('/'))
    resp.set_cookie('session', '', expires=0)
    return resp

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
