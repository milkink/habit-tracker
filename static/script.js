document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('habit-form');
    const habitNameInput = document.getElementById('habit-name');
    const habitFrequencyInput = document.getElementById('habit-frequency');
    const habitList = document.getElementById('habit-list');

    // Function to fetch and display habits
    function fetchHabits() {
        fetch('/get_habits')
            .then(response => response.json())
            .then(data => {
                habitList.innerHTML = '';
                data.habits.forEach(habit => {
                    const li = document.createElement('li');
                    li.textContent = `${habit[1]} - ${habit[2]} - Streak: ${habit[4]}`;

                    // Create remove button
                    const removeButton = document.createElement('button');
                    removeButton.textContent = 'Remove';
                    removeButton.onclick = () => removeHabit(habit[0]);

                    // Create checkbox
                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.checked = habit[3] === 1;
                    checkbox.addEventListener('change', () => updateHabitCompletion(habit[0], checkbox.checked));

                    // Append elements to list item
                    li.prepend(checkbox);
                    li.appendChild(removeButton);
                    habitList.appendChild(li);
                });
            });
    }

    // Fetch habits on page load
    fetchHabits();

    // Handle form submission
    form.addEventListener('submit', function (event) {
        event.preventDefault();
        const habitName = habitNameInput.value.trim();
        const habitFrequency = habitFrequencyInput.value.trim();

        if (!habitName || !habitFrequency) {
            alert('Please fill out both fields.');
            return;
        }

        // Send the new habit to the backend
        fetch('/add_habit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ habit_name: habitName, habit_frequency: habitFrequency })
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            fetchHabits();  // Refresh the list of habits
            habitNameInput.value = '';  // Clear input fields
            habitFrequencyInput.value = '';
        });
    });

    // Function to update habit completion
    function updateHabitCompletion(habitId, isCompleted) {
        fetch(`/update_habit_completion/${habitId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ is_completed: isCompleted })
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            fetchHabits();  // Refresh the list of habits
        });
    }

    // Function to remove a habit
    function removeHabit(habitId) {
        fetch(`/remove_habit/${habitId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            fetchHabits();  // Refresh the list of habits
        });
    }

    // Initialize FullCalendar
    $('#calendar').fullCalendar({
        events: function(start, end, timezone, callback) {
            $.ajax({
                url: '/habits_on_date/' + '{{ current_user.id }}',  // Adjusted to fetch habits for a specific user
                dataType: 'json',
                success: function(data) {
                    var events = data.map(function(habit) {
                        return {
                            title: habit[0] + ' - ' + (habit[1] ? 'Completed' : 'Not Completed'),
                            start: habit[2], // Use the habit completion date
                            allDay: true,
                            color: habit[1] ? 'green' : 'red' // Green for completed, red for not
                        };
                    });
                    callback(events);
                }
            });
        },
        editable: true,
        droppable: false,  // Disallow drag-and-drop
        header: {
            left: 'prev,next today',
            center: 'title',
            right: 'month,agendaWeek,agendaDay'
        },
        dayClick: function(date, jsEvent, view) {
            const selectedDate = date.format(); // Format date as 'YYYY-MM-DD'
            // Show prompt to update habit status for that day
            if (confirm("Update your habit status for " + selectedDate)) {
                // Prompt for habit ID and completion status
                let habitId = prompt("Enter Habit ID (this can be fetched dynamically)");
                let isCompleted = confirm("Mark as completed?");

                // Send this data to the backend to update habit completion for that date
                fetch('/update_habit_status', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        habit_id: habitId,
                        completion_date: selectedDate,
                        is_completed: isCompleted
                    })
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    $('#calendar').fullCalendar('refetchEvents'); // Re-fetch events after status update
                });
            }
        }
    });
});
