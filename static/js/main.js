// Main initialization
$(document).ready(function() {
    // Initialize toastr options
    toastr.options = {
        closeButton: true,
        progressBar: true,
        positionClass: "toast-top-right",
        timeOut: 3000
    };

    // Initialize features based on current page
    if ($('#calendar').length) {
        initializeCalendar();
    }

    if ($('#analytics-container').length) {
        initializeAnalytics(chartData, streakData);
    }

    // Initialize common features
    loadNotifications();
    fetchSuggestedHabits();
    loadAchievements();

    // Initialize event handlers
    handleHabitCheckboxChange();
    handleHabitFormSubmission();
    handleHabitRemoval();
    handleNoteSaving();
    handleSuggestionAddition();

    // Modal overlay click handler
    $('#modal-overlay').on('click', closeModal);

    // Initialize dark mode
    initializeDarkMode();
});

// Dark mode functionality
function initializeDarkMode() {
    // Check for saved dark mode preference
    const darkMode = localStorage.getItem('darkMode') === 'true';
    
    // Apply dark mode if saved preference exists
    if (darkMode) {
        $('body').addClass('dark-mode');
        $('#darkModeToggle').prop('checked', true);
    }

    // Handle dark mode toggle
    $('#darkModeToggle').on('change', function() {
        if ($(this).is(':checked')) {
            $('body').addClass('dark-mode');
            localStorage.setItem('darkMode', 'true');
        } else {
            $('body').removeClass('dark-mode');
            localStorage.setItem('darkMode', 'false');
        }
    });
}
