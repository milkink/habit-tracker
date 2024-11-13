from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import sqlite3
from datetime import datetime, timedelta
import os
import psycopg2

# Retrieve the DATABASE_URL environment variable
DATABASE_URL = os.getenv('DATABASE_URL')

def connect_db():
    # Connect to the PostgreSQL database using the connection string
    conn = psycopg2.connect(DATABASE_URL)
    return conn


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For session management
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirect to login page if not logged in
bcrypt = Bcrypt(app)

# Function to connect to the database
def connect_db():
    return sqlite3.connect('habit_tracker.db')

# User model
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

# Load user
@login_manager.user_loader
def load_user(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(id=user[0], username=user[1])
    return None

# Home route - renders the homepage
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))  # Redirect to the dashboard if logged in
    return render_template('index.html')  # Show Sign Up/Login options if not logged in

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()

        flash("Account created successfully! Please log in.")
        return redirect(url_for('login'))
    return render_template('signup.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user[2], password):
            user_obj = User(id=user[0], username=user[1])
            login_user(user_obj)
            return redirect(url_for('dashboard'))  # Redirect to dashboard after successful login
        else:
            flash('Invalid username or password')
    return render_template('login.html')

# Dashboard route (only accessible if logged in)
@app.route('/dashboard')
@login_required
def dashboard():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, habit_name, habit_frequency, is_completed, streak FROM habits WHERE user_id = ?", (current_user.id,))
    habits = cursor.fetchall()
    conn.close()

    return render_template('dashboard.html', habits=habits)  # Pass habits to template

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))  # Redirect to home after logout

# Initialize the database
# Initialize the database
def init_db():
    conn = connect_db()
    cursor = conn.cursor()
    
    # Create the users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # Create the habits table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        habit_name TEXT NOT NULL,
        habit_frequency TEXT NOT NULL,
        is_completed INTEGER DEFAULT 0,
        streak INTEGER DEFAULT 0,
        last_completed DATE,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    # Create the habit_completions table with a unique constraint on (habit_id, user_id, completion_date)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS habit_completions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        habit_id INTEGER NOT NULL,
        completion_date DATE NOT NULL,
        is_completed BOOLEAN NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (habit_id) REFERENCES habits(id),
        CONSTRAINT unique_habit_completion UNIQUE (habit_id, user_id, completion_date)
    )
    """)

    conn.commit()
    conn.close()


# Adding a new habit
@app.route('/add_habit', methods=['POST'])
@login_required
def add_habit():
    habit_name = request.json['habit_name']
    habit_frequency = request.json['habit_frequency']
    
    # Insert the habit into the database
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO habits (user_id, habit_name, habit_frequency) VALUES (?, ?, ?)",
                   (current_user.id, habit_name, habit_frequency))
    conn.commit()
    conn.close()

    return {'message': 'Habit added successfully!'}

# Display user's habits
@app.route('/get_habits')
@login_required
def get_habits():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, habit_name, habit_frequency, is_completed, streak FROM habits WHERE user_id = ?", (current_user.id,))
    habits = cursor.fetchall()
    conn.close()

    return {'habits': habits}

# Remove a habit
@app.route('/remove_habit/<int:habit_id>', methods=['DELETE'])
@login_required
def remove_habit(habit_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM habits WHERE id = ? AND user_id = ?", (habit_id, current_user.id))
    conn.commit()
    conn.close()

    return {'message': 'Habit removed successfully!'}

# Add a new route for updating habit completion and calculating streak
@app.route('/update_habit_completion/<int:habit_id>', methods=['PUT'])
@login_required
def update_habit_completion(habit_id):
    is_completed = request.json['is_completed']
    current_date = datetime.now().date()

    conn = connect_db()
    cursor = conn.cursor()

    # Check if the habit completion for today already exists
    cursor.execute("""
        SELECT * FROM habit_completions
        WHERE habit_id = ? AND user_id = ? AND completion_date = ?
    """, (habit_id, current_user.id, current_date))
    existing_completion = cursor.fetchone()

    if existing_completion:
        # If record exists, update the completion status
        cursor.execute("""
            UPDATE habit_completions
            SET is_completed = ?
            WHERE habit_id = ? AND user_id = ? AND completion_date = ?
        """, (is_completed, habit_id, current_user.id, current_date))
    else:
        # If record doesn't exist, insert a new completion record
        cursor.execute("""
            INSERT INTO habit_completions (habit_id, user_id, completion_date, is_completed)
            VALUES (?, ?, ?, ?)
        """, (habit_id, current_user.id, current_date, is_completed))

    # Now, handle streak logic
    cursor.execute("SELECT * FROM habits WHERE id = ? AND user_id = ?", (habit_id, current_user.id))
    habit = cursor.fetchone()

    if habit:
        last_completed = habit[6]  # Assuming last_completed is the 7th column in the table

        if is_completed:
            # Check if the habit was completed yesterday, or if this is a fresh streak
            if last_completed is None:
                # If habit has never been completed, start streak at 1
                cursor.execute("UPDATE habits SET streak = 1, last_completed = ? WHERE id = ? AND user_id = ?",
                               (current_date, habit_id, current_user.id))
            elif (current_date - datetime.strptime(last_completed, '%Y-%m-%d').date()).days == 1:
                # If completed yesterday, increment streak
                cursor.execute("UPDATE habits SET streak = streak + 1, last_completed = ? WHERE id = ? AND user_id = ?",
                               (current_date, habit_id, current_user.id))
            else:
                # If not completed yesterday, reset streak to 1
                cursor.execute("UPDATE habits SET streak = 1, last_completed = ? WHERE id = ? AND user_id = ?",
                               (current_date, habit_id, current_user.id))
        else:
            # If not completed today, do not change streak
            cursor.execute("UPDATE habits SET last_completed = ? WHERE id = ? AND user_id = ?",
                           (current_date, habit_id, current_user.id))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Habit completion status updated successfully!'})



# Fetch habits completed on a specific date
@app.route('/habits_on_date/<date>', methods=['GET'])
@login_required
def habits_on_date(date):
    conn = connect_db()
    cursor = conn.cursor()

    # Fetch all habits and their completion status for the selected date
    cursor.execute(""" 
        SELECT habits.habit_name, 
               COALESCE(habit_completions.is_completed, 0) AS is_completed,
               habit_completions.completion_date
        FROM habits
        LEFT JOIN habit_completions 
        ON habits.id = habit_completions.habit_id 
           AND habit_completions.completion_date = ?
        WHERE habits.user_id = ?
    """, (date, current_user.id))

    habits = cursor.fetchall()
    conn.close()

    # Ensure the data is returned in the correct format
    habit_data = [{
        'habit_name': habit[0], 
        'is_completed': habit[1],
        'completion_date': habit[2]
    } for habit in habits]

    return jsonify(habit_data)



@app.route('/habits_on_date_range', methods=['POST'])
@login_required
def habits_on_date_range():
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    print(f"Fetching habits from {start_date} to {end_date}")  # Debugging line

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT habits.habit_name, habit_completions.completion_date, habit_completions.is_completed
        FROM habit_completions
        JOIN habits ON habits.id = habit_completions.habit_id
        WHERE habit_completions.user_id = ? AND habit_completions.completion_date BETWEEN ? AND ?
    """, (current_user.id, start_date, end_date))

    habits = [{'name': row[0], 'date': row[1], 'is_completed': row[2]} for row in cursor.fetchall()]
    conn.close()

    return jsonify(habits)



# Update habit completion for a specific date
@app.route('/update_habit_status', methods=['POST'])
@login_required
def update_habit_status():
    """Update the completion status of a habit for a given date."""
    habit_id = request.json['habit_id']
    completion_date = request.json['completion_date']  # e.g., '2024-11-12'
    is_completed = request.json['is_completed']

    conn = connect_db()
    cursor = conn.cursor()

    # Insert or update the habit completion status for the selected date
    cursor.execute("""
        INSERT OR REPLACE INTO habit_completions (user_id, habit_id, completion_date, is_completed)
        VALUES (?, ?, ?, ?)
    """, (current_user.id, habit_id, completion_date, is_completed))
    
    conn.commit()
    conn.close()

    return jsonify({'message': 'Habit status updated successfully!'})

# Calendar route to display the habit completion calendar
@app.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
