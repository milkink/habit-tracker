import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For session management
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirect to login page if not logged in
bcrypt = Bcrypt(app)

# Function to connect to the database using DATABASE_URL environment variable
def connect_db():
    DATABASE_URL = os.getenv('DATABASE_URL')  # Get the database URL from environment variables
    conn = psycopg2.connect(DATABASE_URL)  # Connect to PostgreSQL
    return conn

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
def init_db():
    conn = connect_db()
    cursor = conn.cursor()
    
    # Create the users table
    cursor.execute(""" 
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,  # Change from INTEGER PRIMARY KEY to SERIAL for PostgreSQL
        username TEXT NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # Create the habits table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS habits (
        id SERIAL PRIMARY KEY,  # Change from INTEGER PRIMARY KEY to SERIAL for PostgreSQL
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
        id SERIAL PRIMARY KEY,  # Change from INTEGER PRIMARY KEY to SERIAL for PostgreSQL
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

@app.route('/add_habit', methods=['POST'])
@login_required
def add_habit():
    habit_name = request.json['habit_name']
    habit_frequency = request.json['habit_frequency']
    
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO habits (user_id, habit_name, habit_frequency) VALUES (%s, %s, %s)",
                   (current_user.id, habit_name, habit_frequency))  # Use %s for PostgreSQL
    conn.commit()
    conn.close()

    return {'message': 'Habit added successfully!'}

# You can update other routes in the same way by replacing SQLite commands with PostgreSQL commands.
# Make sure to use %s instead of ? for placeholders in SQL queries.

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
