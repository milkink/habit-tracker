from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import sqlite3

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
def init_db():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL
    )
    """)
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
from datetime import datetime, timedelta

@app.route('/update_habit_completion/<int:habit_id>', methods=['PUT'])
@login_required
def update_habit_completion(habit_id):
    is_completed = request.json['is_completed']

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM habits WHERE id = ? AND user_id = ?", (habit_id, current_user.id))
    habit = cursor.fetchone()

    if habit:
        last_completed = habit[6]  # Assuming last_completed is the 7th column in the table
        current_date = datetime.now().date()

        # Convert last_completed from string to date if it's not None
        if last_completed:
            last_completed = datetime.strptime(last_completed, '%Y-%m-%d').date()
        
        if is_completed:
            if last_completed is None or current_date > last_completed:
                # Check if completion is consecutive or a new start
                if last_completed == current_date - timedelta(days=1):
                    cursor.execute("UPDATE habits SET streak = streak + 1 WHERE id = ? AND user_id = ?", 
                                   (habit_id, current_user.id))
                else:
                    cursor.execute("UPDATE habits SET streak = 1 WHERE id = ? AND user_id = ?", 
                                   (habit_id, current_user.id))

                # Update last_completed to today
                cursor.execute("UPDATE habits SET last_completed = ?, is_completed = ? WHERE id = ? AND user_id = ?", 
                               (current_date, 1, habit_id, current_user.id))
        else:
            cursor.execute("UPDATE habits SET is_completed = 0 WHERE id = ? AND user_id = ?", 
                           (habit_id, current_user.id))
        
        conn.commit()
        conn.close()

        return jsonify({'message': 'Habit completion status updated successfully!'})

    return jsonify({'message': 'Habit not found or you do not have access to this habit'}), 404


# Function to get streak of a habit
@app.route('/get_streak/<int:habit_id>', methods=['GET'])
@login_required
def get_streak(habit_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT streak FROM habits WHERE id = ? AND user_id = ?", (habit_id, current_user.id))
    streak = cursor.fetchone()
    conn.close()

    if streak:
        return jsonify({'streak': streak[0]})
    else:
        return jsonify({'message': 'Habit not found or you do not have access to this habit'}), 404

# Function to calculate streak (you may want to add logic here depending on your app needs)
@app.route('/calculate_streak/<int:habit_id>', methods=['GET'])
@login_required
def calculate_streak(habit_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT streak, is_completed FROM habits WHERE id = ? AND user_id = ?", (habit_id, current_user.id))
    habit = cursor.fetchone()
    conn.close()

    if habit:
        streak, is_completed = habit
        if is_completed:
            return jsonify({'streak': streak})
        else:
            # If the habit was not completed, reset the streak
            return jsonify({'streak': 0})
    else:
        return jsonify({'message': 'Habit not found or you do not have access to this habit'}), 404


if __name__ == '__main__':
    init_db()
    app.run(debug=True)

