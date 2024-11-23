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
