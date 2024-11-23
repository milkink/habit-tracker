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

// Dark mode functionality using DarkReader
function initializeDarkMode() {
    // Check saved preference
    const isDark = localStorage.getItem('darkMode') === 'true';
    
    // Set initial state
    if (isDark) {
        DarkReader.enable();
        $('#darkModeToggle').prop('checked', true);
    }

    // Handle toggle
    $('#darkModeToggle').on('change', function() {
        if ($(this).is(':checked')) {
            DarkReader.enable();
            localStorage.setItem('darkMode', 'true');
        } else {
            DarkReader.disable();
            localStorage.setItem('darkMode', 'false');
        }
    });
}
