// Calendar initialization and functions
function initializeCalendar() {
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) return;

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth'
        },
        height: 'auto',
        events: '/get_habits',
        eventDidMount: function(info) {
            info.el.style.cursor = 'pointer';
        },
        dateClick: function(info) {
            fetchHabitsForDate(info.dateStr);
        },
        eventClick: function(info) {
            const dateStr = info.event.start.toISOString().split('T')[0];
            fetchHabitsForDate(dateStr);
        },
        eventContent: function(arg) {
            return {
                html: `<div class="fc-event-main-frame">
                    <div class="fc-event-title-container">
                        <div class="fc-event-title fc-sticky">${arg.event.title}</div>
                    </div>
                </div>`
            };
        }
    });

    calendar.render();
}

function fetchHabitsForDate(date) {
    fetch('/habits_on_date/' + date)
        .then(response => response.json())
        .then(data => {
            displayHabitsInModal(date, data);
        })
        .catch(error => {
            console.error('Error fetching habits:', error);
        });
}

function displayHabitsInModal(date, habits) {
    const habitList = document.getElementById('habit-list');
    const modalDate = document.getElementById('modal-date');
    const formattedDate = new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    
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
