from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
import os

# Initialize Flask app and configuration
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For session management
bcrypt = Bcrypt(app)

# Configure SQLAlchemy with PostgreSQL connection string
DATABASE_URL = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy and Flask-Login
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirect to login page if not logged in

# Define User model using SQLAlchemy ORM
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Define Habit model
class Habit(db.Model):
    __tablename__ = 'habits'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    habit_name = db.Column(db.String(150), nullable=False)
    habit_frequency = db.Column(db.String(50), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    streak = db.Column(db.Integer, default=0)
    last_completed = db.Column(db.Date)

# Define HabitCompletion model
class HabitCompletion(db.Model):
    __tablename__ = 'habit_completions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    habit_id = db.Column(db.Integer, db.ForeignKey('habits.id'), nullable=False)
    completion_date = db.Column(db.Date, nullable=False)
    is_completed = db.Column(db.Boolean, nullable=False)

# Initialize the database if needed
with app.app_context():
    db.create_all()  # Creates tables based on defined models

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        flash("Account created successfully! Please log in.")
        return redirect(url_for('login'))
    return render_template('signup.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))  # Redirect to dashboard after successful login
        else:
            flash('Invalid username or password')
    return render_template('login.html')

# Dashboard route (only accessible if logged in)
@app.route('/dashboard')
@login_required
def dashboard():
    habits = Habit.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', habits=habits)  # Pass habits to template

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))  # Redirect to home after logout

# Adding a new habit
@app.route('/add_habit', methods=['POST'])
@login_required
def add_habit():
    habit_name = request.json['habit_name']
    habit_frequency = request.json['habit_frequency']
    
    # Insert the habit into the database
    new_habit = Habit(user_id=current_user.id, habit_name=habit_name, habit_frequency=habit_frequency)
    db.session.add(new_habit)
    db.session.commit()

    return {'message': 'Habit added successfully!'}

# Display user's habits
@app.route('/get_habits')
@login_required
def get_habits():
    habits = Habit.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': habit.id, 
        'habit_name': habit.habit_name,
        'habit_frequency': habit.habit_frequency,
        'is_completed': habit.is_completed,
        'streak': habit.streak
    } for habit in habits])

# Remove a habit
@app.route('/remove_habit/<int:habit_id>', methods=['DELETE'])
@login_required
def remove_habit(habit_id):
    habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first()
    if habit:
        db.session.delete(habit)
        db.session.commit()
        return {'message': 'Habit removed successfully!'}
    return {'message': 'Habit not found'}, 404

# Update habit completion and calculate streak
@app.route('/update_habit_completion/<int:habit_id>', methods=['PUT'])
@login_required
def update_habit_completion(habit_id):
    is_completed = request.json['is_completed']
    current_date = datetime.now().date()

    # Check if the habit completion for today already exists
    completion = HabitCompletion.query.filter_by(
        habit_id=habit_id, user_id=current_user.id, completion_date=current_date).first()

    if completion:
        # Update the completion status
        completion.is_completed = is_completed
    else:
        # Insert a new completion record
        completion = HabitCompletion(
            habit_id=habit_id, user_id=current_user.id, completion_date=current_date, is_completed=is_completed)
        db.session.add(completion)

    # Update streak logic
    habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first()
    if habit:
        if is_completed:
            if habit.last_completed is None:
                habit.streak = 1
            elif (current_date - habit.last_completed).days == 1:
                habit.streak += 1
            else:
                habit.streak = 1
            habit.last_completed = current_date
        else:
            habit.last_completed = current_date

    db.session.commit()
    return jsonify({'message': 'Habit completion status updated successfully!'})

# Fetch habits completed on a specific date
@app.route('/habits_on_date/<date>', methods=['GET'])
@login_required
def habits_on_date(date):
    habits = Habit.query.join(HabitCompletion, Habit.id == HabitCompletion.habit_id).filter(
        Habit.user_id == current_user.id,
        HabitCompletion.completion_date == date
    ).all()
    
    return jsonify([{
        'habit_name': habit.habit_name, 
        'is_completed': habit_completion.is_completed,
        'completion_date': habit_completion.completion_date
    } for habit in habits for habit_completion in habit.habit_completions if habit_completion.completion_date == date])

# Update habit completion for a specific date
@app.route('/update_habit_status', methods=['POST'])
@login_required
def update_habit_status():
    habit_id = request.json['habit_id']
    completion_date = datetime.strptime(request.json['completion_date'], '%Y-%m-%d').date()
    is_completed = request.json['is_completed']

    # Insert or update the habit completion status for the selected date
    completion = HabitCompletion.query.filter_by(
        user_id=current_user.id, habit_id=habit_id, completion_date=completion_date).first()
    
    if completion:
        completion.is_completed = is_completed
    else:
        new_completion = HabitCompletion(
            user_id=current_user.id, habit_id=habit_id, completion_date=completion_date, is_completed=is_completed)
        db.session.add(new_completion)

    db.session.commit()
    return jsonify({'message': 'Habit status updated successfully!'})

# Calendar route to display the habit completion calendar
@app.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')

# Sample route to check data in database
@app.route("/check-data")
def check_data():
    result = db.session.execute("SELECT * FROM users LIMIT 5").fetchall()
    return jsonify([dict(row) for row in result])

if __name__ == '__main__':
    app.run(debug=True)
