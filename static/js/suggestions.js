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
