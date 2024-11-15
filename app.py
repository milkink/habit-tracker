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

@app.route('/analytics')
@login_required
def analytics():
    try:
        # Get the date for 30 days ago
        thirty_days_ago = datetime.now() - timedelta(days=30)
        thirty_days_ago = thirty_days_ago.date()

        # Query habit completions for the logged-in user from the last 30 days
        habit_completions = HabitCompletion.query.filter(
            HabitCompletion.user_id == current_user.id,
            HabitCompletion.completion_date >= thirty_days_ago
        ).all()

        # Initialize data structures to hold habit completion counts
        habits_data = {}
        habits_completion_data = {}  # Store completion data for each habit

        for completion in habit_completions:
            habit_name = completion.habit.habit_name
            habit_id = completion.habit.id
            date = completion.completion_date
            is_completed = completion.is_completed

            # Initialize habit data
            if habit_name not in habits_data:
                habits_data[habit_name] = {
                    'dates': [],  # List to store the dates of completion
                    'completed': 0,  # Counter for completed days
                    'not_completed': 0  # Counter for not completed days
                }

            if habit_id not in habits_completion_data:
                habits_completion_data[habit_id] = [0] * 30  # Initialize with 0 for 30 days

            # Count completions and non-completions
            index = (date - thirty_days_ago).days
            if 0 <= index < 30:  # Ensure index is within the 30-day range
                if is_completed:
                    habits_completion_data[habit_id][index] = 1
                    habits_data[habit_name]['completed'] += 1
                else:
                    habits_data[habit_name]['not_completed'] += 1

            habits_data[habit_name]['dates'].append(date.strftime('%Y-%m-%d'))

        # Prepare the data for Chart.js
        chart_data = {
            'labels': [f"{(datetime.now() - timedelta(days=i)).date()}" for i in range(30)],
            'datasets': []
        }

        # Loop through each habit and create a dataset for it
        for habit_name, data in habits_data.items():
            dataset = {
                'label': habit_name,
                'data': [
                    habits_completion_data.get(habit_name, [0] * 30)[i]  # Safeguard to prevent 'None'
                    for i in range(30)
                ],
                'borderColor': 'rgba(75, 192, 192, 1)',
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'fill': False,
            }
            chart_data['datasets'].append(dataset)

        # Check the chart_data output for correctness
        print(chart_data)

        # Return the template with the individual habit graphs and data
        return render_template('analytics.html', habits_data=habits_data, habits_completion_data=habits_completion_data, chart_data=chart_data)

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

    # Find the completion for today
    completion = HabitCompletion.query.filter_by(
        habit_id=habit_id, user_id=current_user.id, completion_date=current_date).first()

    # Get the habit to update its streak
    habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first()

    if completion:
        # If the habit was already completed today, prevent further updates
        if completion.is_completed == is_completed:
            return jsonify({'message': 'Habit completion already updated for today.'}), 400
        completion.is_completed = is_completed
    else:
        # If there's no completion for today, create a new one
        completion = HabitCompletion(
            habit_id=habit_id, user_id=current_user.id, completion_date=current_date, is_completed=is_completed)
        db.session.add(completion)

    if habit:
        if is_completed:
            # Check if the streak has already been updated for today
            if habit.last_completed and habit.last_completed.date() == current_date:
                # Streak has already been updated today, don't change it again
                return jsonify({'message': 'Streak already updated for today.'}), 400

            if habit.last_completed is None:
                # If there's no record of the last completion, start the streak
                habit.streak = 1
            else:
                # Calculate time difference from the last completion (in hours)
                time_since_last_completion = (datetime.now() - habit.last_completed).total_seconds() / 3600

                if time_since_last_completion <= 24:
                    # If completed within 24 hours, the streak stays the same
                    pass
                elif time_since_last_completion > 24 and time_since_last_completion <= 48:
                    # If 24-48 hours passed (missed 1 day), increment the streak
                    habit.streak += 1
                else:
                    # If more than 48 hours passed without completion, reset the streak
                    habit.streak = 0

            # Update last completed date to today
            habit.last_completed = datetime.now()

        else:
            # If habit is marked as not completed, reset last completed date to today
            habit.last_completed = datetime.now()

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
