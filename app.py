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
    habit = db.relationship('Habit', backref='habit_completions')

# Initialize the database if needed
with app.app_context():
    db.create_all()

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Function to ensure all values are JSON serializable
def ensure_serializable(data):
    """ Recursively ensure that all values in the dictionary are serializable to JSON """
    if isinstance(data, dict):
        return {key: ensure_serializable(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [ensure_serializable(item) for item in data]
    elif isinstance(data, datetime):
        return data.strftime('%Y-%m-%d')  # Handle datetime objects
    else:
        return data  # Return other types as-is

# Home route
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

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
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    try:
        habits = Habit.query.filter_by(user_id=current_user.id).all()
        return render_template('dashboard.html', habits=habits)
    except Exception as e:
        app.logger.error(f"Error loading dashboard: {e}")
        flash("An error occurred while loading the dashboard.")
        return redirect(url_for('home'))

# Analytics route
@app.route('/analytics')
@login_required
def analytics():
    try:
        habit_completions = HabitCompletion.query.filter_by(user_id=current_user.id).all()

        habits_data = {}
        for completion in habit_completions:
            habit_name = completion.habit.habit_name  # Ensure habit_name exists and is not None
            date = completion.completion_date
            is_completed = completion.is_completed

            if habit_name not in habits_data:
                habits_data[habit_name] = {'dates': [], 'completed': [], 'not_completed': []}

            habits_data[habit_name]['dates'].append(date.strftime('%Y-%m-%d'))
            if is_completed:
                habits_data[habit_name]['completed'].append(date.strftime('%Y-%m-%d'))
            else:
                habits_data[habit_name]['not_completed'].append(date.strftime('%Y-%m-%d'))

        # Clean habits_data to ensure no non-serializable types
        cleaned_habits_data = ensure_serializable(habits_data)

        # Log cleaned data for debugging
        app.logger.debug(f"Cleaned Habits Data (After Serialization): {cleaned_habits_data}")

        # Pass cleaned data to the template
        return render_template('analytics.html', habits_data=cleaned_habits_data)

    except Exception as e:
        app.logger.error(f"Error in analytics route: {e}")
        flash("An error occurred while loading the analytics.")
        return redirect(url_for('home'))


# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# Adding a new habit
@app.route('/add_habit', methods=['POST'])
@login_required
def add_habit():
    habit_name = request.json.get('habit_name')
    habit_frequency = request.json.get('habit_frequency')
    new_habit = Habit(user_id=current_user.id, habit_name=habit_name, habit_frequency=habit_frequency)
    db.session.add(new_habit)
    db.session.commit()
    return jsonify({'message': 'Habit added successfully!'}), 200

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
    # Get the habit for the current user
    habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first()
    
    if habit:
        # Delete the habit completions for the current user
        HabitCompletion.query.filter_by(habit_id=habit_id, user_id=current_user.id).delete()

        # Now, delete the habit itself
        db.session.delete(habit)
        db.session.commit()

        return jsonify({"message": "Habit removed successfully!"}), 200
    else:
        return jsonify({"message": "Habit not found."}), 404


# Update habit completion
@app.route('/update_habit_completion/<int:habit_id>', methods=['PUT'])
@login_required
def update_habit_completion(habit_id):
    is_completed = request.json['is_completed']
    current_date = datetime.now().date()

    completion = HabitCompletion.query.filter_by(
        habit_id=habit_id, user_id=current_user.id, completion_date=current_date).first()

    if completion:
        completion.is_completed = is_completed
    else:
        completion = HabitCompletion(
            habit_id=habit_id, user_id=current_user.id, completion_date=current_date, is_completed=is_completed)
        db.session.add(completion)

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
    date_obj = datetime.strptime(date, '%Y-%m-%d').date()
    habit_completions = HabitCompletion.query.join(Habit).filter(
        Habit.user_id == current_user.id,
        HabitCompletion.completion_date == date_obj
    ).all()

    result = [{
        'habit_name': habit_completion.habit.habit_name,
        'is_completed': habit_completion.is_completed,
        'completion_date': habit_completion.completion_date
    } for habit_completion in habit_completions]

    return jsonify(result)

# Calendar route (needed for the link in dashboard.html)
@app.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')

# Update habit completion for a specific date
@app.route('/update_habit_status', methods=['POST'])
@login_required
def update_habit_status():
    data = request.get_json()
    habit_id = data.get("habit_id")
    date_str = data.get("completion_date")
    is_completed = data.get("is_completed")

    completion_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    completion = HabitCompletion.query.filter_by(habit_id=habit_id, user_id=current_user.id, completion_date=completion_date).first()

    if completion:
        completion.is_completed = is_completed
    else:
        completion = HabitCompletion(
            habit_id=habit_id,
            user_id=current_user.id,
            completion_date=completion_date,
            is_completed=is_completed
        )
        db.session.add(completion)

    db.session.commit()
    return jsonify({'message': 'Habit status updated successfully!'})

if __name__ == '__main__':
    app.run(debug=True)
