from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
import os
from datetime import datetime, timedelta
import json
from flask_mail import Mail, Message
import csv
from io import StringIO

# Initialize Flask app and configuration
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") # For session management
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

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    color = db.Column(db.String(7), default='#007bff')  # Hex color code

class HabitCategory(db.Model):
    __tablename__ = 'habit_categories'
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habits.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)

class HabitNote(db.Model):
    __tablename__ = 'habit_notes'
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habits.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    note = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Achievement(db.Model):
    __tablename__ = 'achievements'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    badge_icon = db.Column(db.String(50))  # Font Awesome icon class
    earned_date = db.Column(db.DateTime, default=datetime.utcnow)


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


@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Fetch habits for the logged-in user
        habits = Habit.query.filter_by(user_id=current_user.id).all()

        # Refresh each habit object to ensure we get the latest data (e.g., streak values)
        for habit in habits:
            db.session.refresh(habit)  # Refresh the habit to get the latest streak

        now = datetime.now()  # Get the current datetime once

       

        return render_template('dashboard.html', habits=habits, now=now) 

    except Exception as e:
        app.logger.error(f"Error loading dashboard: {e}")
        flash("An error occurred while loading the dashboard.")
        return redirect(url_for('home'))




@app.route('/analytics')
@login_required
def analytics():
    try:
        thirty_days_ago = datetime.now() - timedelta(days=30)
        thirty_days_ago = thirty_days_ago.date()

        # Initialize data structures for each frequency
        habits_data = {
            'daily': {},
            'weekly': {},
            'monthly': {}
        }
        
        # Query all habit completions
        habit_completions = HabitCompletion.query.join(Habit).filter(
            HabitCompletion.user_id == current_user.id,
            HabitCompletion.completion_date >= thirty_days_ago
        ).order_by(HabitCompletion.completion_date.desc()).all()

        # Process completions by frequency
        for completion in habit_completions:
            habit = completion.habit
            frequency = habit.habit_frequency.lower()
            habit_name = habit.habit_name
            date = completion.completion_date
            is_completed = completion.is_completed

            if habit_name not in habits_data[frequency]:
                habits_data[frequency][habit_name] = {
                    'dates': [],
                    'completed': 0,
                    'not_completed': 0
                }

            habits_data[frequency][habit_name]['dates'].append(date.strftime('%Y-%m-%d'))
            
            if is_completed:
                habits_data[frequency][habit_name]['completed'] += 1
            else:
                habits_data[frequency][habit_name]['not_completed'] += 1

        # Prepare chart data for each frequency
        chart_data = {freq: {'labels': [], 'datasets': []} for freq in ['daily', 'weekly', 'monthly']}
        streak_data = {freq: {'labels': [], 'datasets': []} for freq in ['daily', 'weekly', 'monthly']}

        # Generate date labels (oldest to newest)
        dates = []
        for i in range(30):
            current_date = datetime.now() - timedelta(days=29-i)
            dates.append(current_date.strftime('%Y-%m-%d'))

        for freq in ['daily', 'weekly', 'monthly']:
            chart_data[freq]['labels'] = dates
            streak_data[freq]['labels'] = dates

        # Calculate completion and streak data for each frequency
        for frequency, habits in habits_data.items():
            for habit_name, data in habits.items():
                completion_dataset = {
                    'label': habit_name,
                    'data': [],
                    'borderColor': f'rgba({hash(habit_name) % 256}, {(hash(habit_name) * 2) % 256}, {(hash(habit_name) * 3) % 256}, 1)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    'fill': False
                }
                
                streak_dataset = {
                    'label': f'{habit_name} Streak',
                    'data': [],
                    'borderColor': f'rgba({hash(habit_name) % 256}, {(hash(habit_name) * 2) % 256}, {(hash(habit_name) * 3) % 256}, 1)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    'fill': False
                }

                current_streak = 0
                completed_dates = set(data['dates'])

                if frequency == 'daily':
                    for date in dates:
                        if date in completed_dates:
                            current_streak += 1
                        else:
                            current_streak = 0
                        streak_dataset['data'].append(current_streak)
                        completion_dataset['data'].append(1 if date in completed_dates else 0)

                elif frequency == 'weekly':
                    # Initialize variables for weekly tracking
                    current_week = None
                    week_completions = {}
                    
                    for date in dates:
                        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                        week_start = date_obj - timedelta(days=date_obj.weekday())
                        week_end = week_start + timedelta(days=6)
                        
                        # Only process once per week
                        if week_start not in week_completions:
                            # Check if there's any completion in this week
                            week_has_completion = any(
                                week_start <= datetime.strptime(d, '%Y-%m-%d').date() <= week_end
                                for d in completed_dates
                            )
                            week_completions[week_start] = week_has_completion
                            
                            if week_has_completion:
                                if current_week is None or (week_start - current_week).days == 7:
                                    current_streak += 1
                                else:
                                    current_streak = 1
                            else:
                                current_streak = 0
                            
                            current_week = week_start
                        
                        # For the graph, show the streak value only on the current date or last day of week
                        if date_obj == datetime.now().date() or date_obj.weekday() == 6:
                            streak_dataset['data'].append(current_streak)
                        else:
                            streak_dataset['data'].append(None)
                        
                        # Set completion status for the entire week
                        completion_dataset['data'].append(1 if week_completions[week_start] else 0)

                elif frequency == 'monthly':
                    # Initialize variables for monthly tracking
                    current_month = None
                    month_completions = {}
                    last_completed_month = None
                    
                    for date in dates:
                        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                        month_key = (date_obj.year, date_obj.month)
                        
                        # Only process once per month
                        if month_key not in month_completions:
                            # Check if there's any completion in this month
                            month_has_completion = any(
                                (datetime.strptime(d, '%Y-%m-%d').date().year,
                                 datetime.strptime(d, '%Y-%m-%d').date().month) == month_key
                                for d in completed_dates
                            )
                            month_completions[month_key] = month_has_completion
                            
                            if month_has_completion:
                                if last_completed_month is None:
                                    current_streak = 1
                                elif (
                                    month_key[0] * 12 + month_key[1] == 
                                    last_completed_month[0] * 12 + last_completed_month[1] + 1
                                ):
                                    current_streak += 1
                                else:
                                    current_streak = 1
                                last_completed_month = month_key
                            else:
                                current_streak = 0
                        
                        # For the graph, show the streak value only on the current date or last day of month
                        is_last_day = date_obj.day == (date_obj.replace(day=1) + timedelta(days=32)).replace(day=1).day - 1
                        if date_obj == datetime.now().date() or is_last_day:
                            streak_dataset['data'].append(current_streak)
                        else:
                            streak_dataset['data'].append(None)
                        
                        # Set completion status for the entire month
                        completion_dataset['data'].append(1 if month_completions[month_key] else 0)

                chart_data[frequency]['datasets'].append(completion_dataset)
                streak_data[frequency]['datasets'].append(streak_dataset)

        return render_template('analytics.html', 
                             habits_data=habits_data,
                             chart_data=chart_data,
                             streak_chart_data=streak_data)

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

@app.route('/remove_habit/<int:habit_id>', methods=['DELETE'])
@login_required
def remove_habit(habit_id):
    try:
        # Get the habit for the current user
        habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first()
        
        if habit:
            # Delete all notes associated with this habit
            HabitNote.query.filter_by(habit_id=habit_id, user_id=current_user.id).delete()
            
            # Delete all habit completions for this habit
            HabitCompletion.query.filter_by(habit_id=habit_id, user_id=current_user.id).delete()
            
            # Delete any habit-category associations
            HabitCategory.query.filter_by(habit_id=habit_id).delete()
            
            # Finally, delete the habit itself
            db.session.delete(habit)
            db.session.commit()

            return jsonify({"message": "Habit and all associated data removed successfully!"}), 200
        else:
            return jsonify({"message": "Habit not found."}), 404

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error removing habit: {e}")
        return jsonify({"message": "An error occurred while removing the habit."}), 500



@app.route('/update_habit_completion/<int:habit_id>', methods=['PUT'])
@login_required
def update_habit_completion(habit_id):
    try:
        is_completed = request.json['is_completed']
        current_date = datetime.now().date()

        habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first()
        if not habit:
            return jsonify({'message': 'Habit not found'}), 404

        completion = HabitCompletion.query.filter_by(
            habit_id=habit_id, 
            user_id=current_user.id, 
            completion_date=current_date
        ).first()

        if not completion:
            completion = HabitCompletion(
                habit_id=habit_id,
                user_id=current_user.id,
                completion_date=current_date,
                is_completed=is_completed
            )
            db.session.add(completion)
        else:
            completion.is_completed = is_completed

        # Update streak based on frequency
        if is_completed:
            if habit.last_completed:
                days_since_last = (current_date - habit.last_completed).days
                
                if habit.habit_frequency.lower() == 'daily':
                    if days_since_last == 1:
                        habit.streak += 1
                    elif days_since_last > 1:
                        habit.streak = 1
                elif habit.habit_frequency.lower() == 'weekly':
                    last_week = habit.last_completed.isocalendar()[1]
                    current_week = current_date.isocalendar()[1]
                    if current_week - last_week == 1:
                        habit.streak += 1
                    elif current_week - last_week > 1:
                        habit.streak = 1
                elif habit.habit_frequency.lower() == 'monthly':
                    last_month = habit.last_completed.month
                    current_month = current_date.month
                    months_diff = (current_date.year - habit.last_completed.year) * 12 + current_month - last_month
                    if months_diff == 1:
                        habit.streak += 1
                    elif months_diff > 1:
                        habit.streak = 1
            else:
                habit.streak = 1
            
            habit.last_completed = current_date

        # Check for new achievements BEFORE committing
        new_achievements = check_achievements(current_user.id, habit_id)
        
        # Commit all changes in one transaction
        db.session.commit()
        
        return jsonify({
            'message': 'Habit completion status updated successfully!',
            'streak': habit.streak,
            'new_achievements': new_achievements
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating habit completion: {e}")
        return jsonify({'message': 'An error occurred while updating habit completion'}), 500

@app.route('/habits_on_date/<date>')
@login_required
def habits_on_date(date):
    try:
        # Convert string date to datetime object
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Query all habits and their completion status for the given date
        habits_query = db.session.query(
            Habit,
            HabitCompletion
        ).outerjoin(
            HabitCompletion,
            db.and_(
                HabitCompletion.habit_id == Habit.id,
                HabitCompletion.completion_date == date_obj
            )
        ).filter(
            Habit.user_id == current_user.id
        ).all()

        habits_data = []
        for habit, completion in habits_query:
            habits_data.append({
                'habit_id': habit.id,
                'habit_name': habit.habit_name,
                'is_completed': completion.is_completed if completion else False
            })

        return jsonify(habits_data)

    except Exception as e:
        app.logger.error(f"Error fetching habits for date {date}: {e}")
        return jsonify({'error': 'Failed to fetch habits'}), 500
        
# Calendar route (needed for the link in dashboard.html)
@app.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')

@app.route('/leaderboard')
@login_required
def leaderboard():
    # Query to calculate total streaks for all users, including those with no streaks
    leaderboard_data = db.session.query(
        User.username,
        db.func.coalesce(db.func.sum(Habit.streak), 0).label('total_streak')
    ).outerjoin(Habit, User.id == Habit.user_id)\
     .group_by(User.username)\
     .order_by(db.desc('total_streak')).all()

    return render_template('leaderboard.html', leaderboard=leaderboard_data)

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


@app.route('/notifications')
@login_required
def notifications():
    try:
        # Define notification logic
        notifications = []

        # Check for streak breaks
        streak_breaks = Habit.query.filter(
            Habit.user_id == current_user.id,
            Habit.last_completed < (datetime.now().date() - timedelta(days=1))
        ).all()

        for habit in streak_breaks:
            notifications.append({
                "message": f"Streak broken for habit '{habit.habit_name}'. Try to rebuild it!"
            })

        # Add notifications for habits completed today
        today_completions = HabitCompletion.query.filter_by(
            user_id=current_user.id,
            completion_date=datetime.now().date(),
            is_completed=True
        ).all()

        for completion in today_completions:
            notifications.append({
                "message": f"Great job completing '{completion.habit.habit_name}' today!"
            })

        return jsonify(notifications), 200

    except Exception as e:
        app.logger.error(f"Error fetching notifications: {e}")
        return jsonify({"error": "Unable to fetch notifications."}), 500


# Suggestions endpoint
@app.route('/suggestions', methods=['GET'])
@login_required
def suggestions():
    # Define a list of suggested habits with unique IDs
    suggested_habits = [
        {"id": 1, "habit_name": "Drink 8 glasses of water", "habit_frequency": "Daily"},
        {"id": 2, "habit_name": "Meditate for 10 minutes", "habit_frequency": "Daily"},
        {"id": 3, "habit_name": "Go for a 30-minute walk", "habit_frequency": "Daily"},
        {"id": 4, "habit_name": "Read for 15 minutes", "habit_frequency": "Daily"},
        {"id": 5, "habit_name": "Write in a journal", "habit_frequency": "Daily"},
        {"id": 6, "habit_name": "Do a 5-minute workout", "habit_frequency": "Daily"},
        {"id": 7, "habit_name": "Plan tomorrow's tasks", "habit_frequency": "Daily"},
        {"id": 8, "habit_name": "Disconnect from screens 1 hour before bed", "habit_frequency": "Daily"}
    ]
    return jsonify(suggested_habits), 200


# Add suggested habit to the user's habits
@app.route('/add_suggestion/<habit_name>', methods=['POST'])
@login_required
def add_suggestion(habit_name):
    habit_frequency = request.json.get('habit_frequency', 'Daily')  # Default to Daily if not provided
    existing_habit = Habit.query.filter_by(user_id=current_user.id, habit_name=habit_name).first()
    
    if existing_habit:
        return jsonify({"message": f"Habit '{habit_name}' already exists in your list."}), 400

    new_habit = Habit(user_id=current_user.id, habit_name=habit_name, habit_frequency=habit_frequency)
    db.session.add(new_habit)
    db.session.commit()
    return jsonify({"message": f"Habit '{habit_name}' has been added to your list!"}), 200

@app.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    if request.method == 'POST':
        name = request.json.get('name')
        color = request.json.get('color', '#007bff')
        category = Category(name=name, color=color, user_id=current_user.id)
        db.session.add(category)
        db.session.commit()
        return jsonify({'message': 'Category added successfully', 'id': category.id})
    
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return jsonify([{'id': c.id, 'name': c.name, 'color': c.color} for c in categories])

@app.route('/habit/<int:habit_id>/notes', methods=['GET', 'POST'])
@login_required
def habit_notes(habit_id):
    if request.method == 'POST':
        note_text = request.json.get('note')
        note = HabitNote(habit_id=habit_id, user_id=current_user.id, note=note_text)
        db.session.add(note)
        db.session.commit()
        return jsonify({'message': 'Note added successfully'})
    
    notes = HabitNote.query.filter_by(habit_id=habit_id, user_id=current_user.id)\
        .order_by(HabitNote.date.desc()).all()
    return jsonify([{
        'id': note.id,
        'note': note.note,
        'date': note.date.strftime('%Y-%m-%d %H:%M')
    } for note in notes])

@app.route('/achievements')
@login_required
def achievements():
    user_achievements = Achievement.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'name': a.name,
        'description': a.description,
        'badge_icon': a.badge_icon,
        'earned_date': a.earned_date.strftime('%Y-%m-%d')
    } for a in user_achievements])

def check_achievements(user_id, habit_id):
    """Check and award achievements based on user's habit completion"""
    try:
        # Get all habits for the user
        habits = Habit.query.filter_by(user_id=user_id).all()
        total_streak = sum(habit.streak for habit in habits)
        
        # Achievement criteria
        achievements = []
        
        # First Habit Achievement
        if len(habits) == 1:
            achievements.append({
                'name': 'Habit Pioneer',
                'description': 'Created your first habit!',
                'badge_icon': 'fa-star'
            })
        
        # Streak Achievements
        streak_achievements = [
            (7, 'Week Warrior', 'Maintained a 7-day streak', 'fa-fire'),
            (30, 'Monthly Master', 'Maintained a 30-day streak', 'fa-crown'),
            (100, 'Habit Hero', 'Maintained a 100-day streak', 'fa-trophy')
        ]
        
        for streak, name, desc, icon in streak_achievements:
            if total_streak >= streak:
                existing = Achievement.query.filter_by(
                    user_id=user_id, name=name).first()
                if not existing:
                    achievements.append({
                        'name': name,
                        'description': desc,
                        'badge_icon': icon
                    })
        
        # Add new achievements to database
        for achievement in achievements:
            new_achievement = Achievement(
                user_id=user_id,
                name=achievement['name'],
                description=achievement['description'],
                badge_icon=achievement['badge_icon']
            )
            db.session.add(new_achievement)
        
        db.session.commit()
        
        return achievements
    except Exception as e:
        app.logger.error(f"Error checking achievements: {e}")
        return []

@app.route('/preferences')
@login_required
def preferences():
    try:
        user_preferences = UserPreference.query.filter_by(user_id=current_user.id).first()
        if not user_preferences:
            user_preferences = UserPreference(user_id=current_user.id)
            db.session.add(user_preferences)
            db.session.commit()
        
        return render_template('preferences.html', 
                             preferences=user_preferences,
                             now=datetime.now())
    except SQLAlchemyError as e:
        logger.error(f"Error loading preferences page: {e}")
        flash("Unable to load preferences. Please try again.", "error")
        return redirect(url_for('dashboard'))




if __name__ == '__main__':
    app.run(debug=True)
