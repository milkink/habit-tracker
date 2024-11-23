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
    initDarkMode();
});

// Dark mode functions
function initDarkMode() {
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    document.documentElement.classList.toggle('dark', isDarkMode);
    
    const toggle = document.getElementById('darkModeToggle');
    if (toggle) {
        toggle.checked = isDarkMode;
    }
}

function toggleDarkMode() {
    const isDarkMode = document.documentElement.classList.toggle('dark');
    localStorage.setItem('darkMode', isDarkMode);
}
