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
});
