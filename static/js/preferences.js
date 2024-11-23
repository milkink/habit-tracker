// Handles user preferences
document.addEventListener('DOMContentLoaded', () => {
  const darkModeToggle = document.getElementById('dark-mode-toggle');
  const emailNotifToggle = document.getElementById('email-notifications-toggle');

  const loadPreferences = async () => {
    try {
      const response = await fetch('/preferences');
      const preferences = await response.json();
      
      darkModeToggle.checked = preferences.dark_mode;
      emailNotifToggle.checked = preferences.email_notifications;
      
      if (preferences.dark_mode) {
        document.body.classList.add('dark-mode');
      }
    } catch (error) {
      console.error('Error loading preferences:', error);
    }
  };

  const updatePreferences = async (preferences) => {
    try {
      await fetch('/preferences', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(preferences)
      });
    } catch (error) {
      console.error('Error updating preferences:', error);
    }
  };

  darkModeToggle?.addEventListener('change', (e) => {
    const darkMode = e.target.checked;
    document.body.classList.toggle('dark-mode', darkMode);
    updatePreferences({ dark_mode: darkMode });
  });

  emailNotifToggle?.addEventListener('change', (e) => {
    updatePreferences({ email_notifications: e.target.checked });
  });

  // Export functionality
  const exportButton = document.getElementById('export-stats');
  exportButton?.addEventListener('click', async () => {
    const startDate = document.getElementById('export-start-date').value;
    const endDate = document.getElementById('export-end-date').value;
    
    window.location.href = `/export_stats?start_date=${startDate}&end_date=${endDate}`;
  });

  // Initial load of preferences
  loadPreferences();
});