// Calendar initialization and functions
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
