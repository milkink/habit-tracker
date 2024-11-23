// Global variables
let currentHabitId = null;

// Document ready handler
$(document).ready(function() {
    loadNotifications();
    fetchSuggestedHabits();
    loadAchievements();

    // Initialize toastr options
    toastr.options = {
        closeButton: true,
        progressBar: true,
        positionClass: "toast-top-right",
        timeOut: 3000
    };

    // Initialize calendar if we're on the calendar page
    if ($('#calendar').length) {
        initializeCalendar();
    }
});

// Calendar initialization
function initializeCalendar() {
    $('#calendar').fullCalendar({
        header: {
            left: 'prev,next today',
            center: 'title',
            right: 'month,agendaWeek,agendaDay'
        },
        events: function(start, end, timezone, callback) {
            $.ajax({
                url: '/get_habits',
                dataType: 'json',
                success: function(data) {
                    var events = [];
                    data.forEach(function(habit) {
                        var eventColor = habit.is_completed ? 'green' : 'red';
                        events.push({
                            title: habit.habit_name,
                            start: habit.completion_date,
                            backgroundColor: eventColor,
                            textColor: 'white',
                            description: habit.habit_name,
                            allDay: true
                        });
                    });
                    callback(events);
                }
            });
        },
        dayClick: function(date, jsEvent, view) {
            var dateStr = date.format('YYYY-MM-DD');
            fetchHabitsForDate(dateStr);
        },
        eventClick: function(calEvent, jsEvent, view) {
            var dateStr = moment(calEvent.start).format('YYYY-MM-DD');
            fetchHabitsForDate(dateStr);
        }
    });
}

// Calendar related functions
function fetchHabitsForDate(date) {
    $.ajax({
        url: '/habits_on_date/' + date,
        method: 'GET',
        success: function(data) {
            displayHabitsInModal(date, data);
        },
        error: function(xhr, status, error) {
            console.error('Error fetching habits:', error);
        }
    });
}

function displayHabitsInModal(date, habits) {
    const habitList = document.getElementById('habit-list');
    const modalDate = document.getElementById('modal-date');
    const formattedDate = moment(date).format('MMMM D, YYYY');
    
    modalDate.textContent = formattedDate;
    habitList.innerHTML = '';

    if (habits && habits.length > 0) {
        habits.forEach(habit => {
            const li = document.createElement('li');
            const statusClass = habit.is_completed ? 'status-completed' : 'status-not-completed';
            const statusText = habit.is_completed ? 'Completed' : 'Not Completed';
            
            li.innerHTML = `
                <span>${habit.habit_name}</span>
                <span class="habit-status ${statusClass}">${statusText}</span>
            `;
            habitList.appendChild(li);
        });
    } else {
        const li = document.createElement('li');
        li.textContent = 'No habits tracked for this date';
        habitList.appendChild(li);
    }

    document.getElementById('modal-overlay').style.display = 'block';
    document.getElementById('habit-modal').style.display = 'block';
}

function closeModal() {
    document.getElementById('modal-overlay').style.display = 'none';
    document.getElementById('habit-modal').style.display = 'none';
}

// Habit management functions
function handleHabitCheckboxChange() {
    $(document).on('change', '.habit-checkbox', function() {
        const habitId = $(this).data('habit-id');
        const isCompleted = $(this).prop('checked') ? 1 : 0;

        $.ajax({
            url: '/update_habit_completion/' + habitId,
            type: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify({ is_completed: isCompleted }),
            success: function(response) {
                if (response.streak !== undefined) {
                    $("#habit-streak-" + habitId).text(response.streak);
                    
                    if (response.new_achievements && response.new_achievements.length > 0) {
                        response.new_achievements.forEach(achievement => {
                            toastr.success(`Achievement Unlocked: ${achievement.name}`);
                        });
                        loadAchievements();
                    }
                } else {
                    alert(response.message);
                }
            },
            error: function(error) {
                alert('Error updating habit completion.');
            }
        });
    });
}

function handleHabitFormSubmission() {
    $('#habit-form').submit(function(e) {
        e.preventDefault();
        const habitName = $('#habit-name').val();
        const habitFrequency = $('#habit-frequency').val();

        if (!habitName || !habitFrequency) {
            alert('Both habit name and frequency are required.');
            return;
        }

        $.ajax({
            url: '/add_habit',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                habit_name: habitName,
                habit_frequency: habitFrequency
            }),
            success: function(response) {
                toastr.success(response.message);
                location.reload();
            },
            error: function(error) {
                toastr.error('Error adding habit.');
            }
        });
    });
}

function handleHabitRemoval() {
    $(document).on('click', '.remove-btn', function() {
        const habitId = $(this).data('habit-id');

        if (confirm('Are you sure you want to remove this habit?')) {
            $.ajax({
                url: '/remove_habit/' + habitId,
                type: 'DELETE',
                success: function(response) {
                    toastr.success(response.message);
                    location.reload();
                },
                error: function(error) {
                    toastr.error('Error removing habit.');
                }
            });
        }
    });
}

// Achievement functions
function loadAchievements() {
    $.get('/achievements', function(achievements) {
        const container = $('#achievements-container');
        container.empty();
        
        achievements.forEach(achievement => {
            container.append(`
                <div class="col-md-3 mb-3">
                    <div class="card achievement-card">
                        <div class="card-body text-center">
                            <i class="fas ${achievement.badge_icon} fa-2x mb-2"></i>
                            <h5 class="card-title">${achievement.name}</h5>
                            <p class="card-text">${achievement.description}</p>
                            <small class="text-muted">Earned: ${achievement.earned_date}</small>
                        </div>
                    </div>
                </div>
            `);
        });
    });
}

// Note functions
function openNoteModal(habitId) {
    currentHabitId = habitId;
    loadPreviousNotes(habitId);
    $('#habitNoteModal').modal('show');
}

function loadPreviousNotes(habitId) {
    $.get(`/habit/${habitId}/notes`, function(notes) {
        const container = $('#previousNotes');
        container.empty();
        
        notes.forEach(note => {
            container.append(`
                <div class="card mb-2">
                    <div class="card-body">
                        <p class="card-text">${note.note}</p>
                        <small class="text-muted">${note.date}</small>
                    </div>
                </div>
            `);
        });
    });
}

function handleNoteSaving() {
    $('#saveNote').click(function() {
        const note = $('#habitNote').val();
        if (note && currentHabitId) {
            $.ajax({
                url: `/habit/${currentHabitId}/notes`,
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ note: note }),
                success: function(response) {
                    $('#habitNote').val('');
                    loadPreviousNotes(currentHabitId);
                    toastr.success('Note added successfully!');
                },
                error: function(error) {
                    toastr.error('Error adding note.');
                }
            });
        }
    });
}

// Notification functions
function loadNotifications() {
    $.ajax({
        url: '/notifications',
        type: 'GET',
        success: function(notifications) {
            const container = $('#notifications-container');
            container.empty();

            if (notifications.length === 0) {
                container.append('<p>No new notifications.</p>');
            } else {
                notifications.forEach(notification => {
                    container.append('<p>' + notification.message + '</p>');
                });
            }
        },
        error: function() {
            $('#notifications-container').html('<p>Error loading notifications.</p>');
        }
    });
}

// Suggestion functions
function fetchSuggestedHabits() {
    $.ajax({
        url: '/suggestions',
        type: 'GET',
        success: function(suggestions) {
            const suggestionsList = $('#suggestions-list');
            suggestionsList.empty();

            if (suggestions.length === 0) {
                suggestionsList.append('<p>No suggestions available.</p>');
            } else {
                suggestions.forEach(suggestion => {
                    suggestionsList.append(`
                        <li class="suggestion-item">
                            <span>${suggestion.habit_name} (${suggestion.habit_frequency})</span>
                            <button class="add-suggestion-btn" 
                                    data-habit-name="${suggestion.habit_name}"
                                    data-habit-frequency="${suggestion.habit_frequency}">
                                Add
                            </button>
                        </li>
                    `);
                });                    
            }
        },
        error: function() {
            $('#suggestions-list').html('<p>Error loading suggestions.</p>');
        }
    });
}

function handleSuggestionAddition() {
    $(document).on('click', '.add-suggestion-btn', function() {
        const habitName = $(this).data('habit-name');
        const habitFrequency = $(this).data('habit-frequency');

        $.ajax({
            url: '/add_suggestion/' + encodeURIComponent(habitName),
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                habit_frequency: habitFrequency
            }),
            success: function(response) {
                toastr.success(response.message);
                location.reload();
            },
            error: function(error) {
                toastr.error('Error adding suggested habit.');
            }
        });
    });
}

// Initialize all event handlers
$(document).ready(function() {
    handleHabitCheckboxChange();
    handleHabitFormSubmission();
    handleHabitRemoval();
    handleNoteSaving();
    handleSuggestionAddition();

    // Modal overlay click handler
    $('#modal-overlay').on('click', closeModal);
});
