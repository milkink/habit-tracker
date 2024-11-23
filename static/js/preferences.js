document.addEventListener('DOMContentLoaded', () => {
  const darkModeToggle = document.getElementById('dark-mode-toggle');
  const emailNotifToggle = document.getElementById('email-notifications-toggle');

  const loadPreferences = async () => {
    try {
      const response = await fetch('/api/preferences');
      const preferences = await response.json();
      
      darkModeToggle.checked = preferences.dark_mode;
      emailNotifToggle.checked = preferences.email_notifications;
      
      if (preferences.dark_mode) {
        document.body.classList.add('dark-mode');
      }
    } catch (error) {
      console.error('Error loading preferences:', error);
      toastr.error('Error loading preferences.');
    }
  };

  const updatePreferences = async (preferences) => {
    try {
      const response = await fetch('/api/preferences', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(preferences)
      });
      
      if (response.ok) {
        toastr.success('Preferences updated successfully!');
      }
    } catch (error) {
      console.error('Error updating preferences:', error);
      toastr.error('Error updating preferences.');
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
    
    if (!startDate || !endDate) {
      toastr.error('Please select both start and end dates.');
      return;
    }
    
    window.location.href = `/export_stats?start_date=${startDate}&end_date=${endDate}`;
  });

  // Initial load of preferences
  loadPreferences();
});
