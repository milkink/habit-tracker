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
                habitList.innerHTML = ''; // Clear the list before adding new items
                data.forEach(habit => {
                    const li = document.createElement('li');
                    li.textContent = `${habit.habit_name} - ${habit.habit_frequency} - Streak: ${habit.streak}`;

                    // Create remove button
                    const removeButton = document.createElement('button');
                    removeButton.textContent = 'Remove';
                    removeButton.onclick = () => removeHabit(habit.id);

                    // Create checkbox
                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.checked = habit.is_completed;
                    checkbox.addEventListener('change', () => updateHabitCompletion(habit.id, checkbox.checked));

                    // Append elements to list item
                    li.prepend(checkbox);
                    li.appendChild(removeButton);
                    habitList.appendChild(li);
                });
            });
    }

    // Fetch habits on page load
    fetchHabits();

    // Handle form submission to add a new habit
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
                url: '/habits_on_date/' + current_user_id,  // Use the dynamic user ID
                dataType: 'json',
                success: function(data) {
                    var events = data.map(function(habit) {
                        return {
                            title: habit.habit_name + ' - ' + (habit.is_completed ? 'Completed' : 'Not Completed'),
                            start: habit.completion_date, // Use the habit completion date
                            allDay: true,
                            color: habit.is_completed ? 'green' : 'red' // Green for completed, red for not
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
            // Fetch habits for the selected date
            fetch(`/habits_on_date/${selectedDate}`)
                .then(response => response.json())
                .then(habits => {
                    // Create the popup content
                    let completedHabits = '';
                    let notCompletedHabits = '';

                    habits.forEach(habit => {
                        if (habit.is_completed) {
                            completedHabits += `<li>${habit.habit_name}</li>`;
                        } else {
                            notCompletedHabits += `<li>${habit.habit_name}</li>`;
                        }
                    });

                    // Display the popup with habit information
                    const popupContent = `
                        <h3>Habits for ${selectedDate}</h3>
                        <h4>Completed:</h4>
                        <ul>${completedHabits || '<li>No habits completed</li>'}</ul>
                        <h4>Not Completed:</h4>
                        <ul>${notCompletedHabits || '<li>No habits pending</li>'}</ul>
                    `;

                    // Create a modal or popup element
                    const popup = document.createElement('div');
                    popup.classList.add('habit-popup');
                    popup.innerHTML = popupContent;

                    // Close button for the popup
                    const closeButton = document.createElement('button');
                    closeButton.textContent = 'Close';
                    closeButton.onclick = () => {
                        popup.style.display = 'none'; // Close the popup
                    };

                    popup.appendChild(closeButton);

                    // Append the popup to the body
                    document.body.appendChild(popup);

                    // Style the popup
                    popup.style.position = 'fixed';
                    popup.style.top = '50%';
                    popup.style.left = '50%';
                    popup.style.transform = 'translate(-50%, -50%)';
                    popup.style.padding = '20px';
                    popup.style.backgroundColor = '#fff';
                    popup.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.1)';
                    popup.style.zIndex = 1000;
                })
                .catch(error => {
                    alert('Failed to fetch habits for this date.');
                    console.error('Error fetching habits for the date:', error);
                });
}

