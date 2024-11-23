// preferences.js
class UserPreferences {
  constructor() {
    this.darkModeToggle = document.getElementById('dark-mode-toggle');
    this.emailNotifToggle = document.getElementById('email-notifications-toggle');
    this.exportButton = document.getElementById('export-stats');
    this.startDateInput = document.getElementById('export-start-date');
    this.endDateInput = document.getElementById('export-end-date');
    
    this.init();
  }

  async init() {
    await this.loadPreferences();
    this.setupEventListeners();
  }

  async loadPreferences() {
    try {
      const response = await fetch('/api/preferences');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const preferences = await response.json();
      
      this.applyPreferences(preferences);
    } catch (error) {
      console.error('Error loading preferences:', error);
      toastr.error('Unable to load preferences. Please try again later.');
    }
  }

  applyPreferences(preferences) {
    if (this.darkModeToggle) {
      this.darkModeToggle.checked = preferences.dark_mode;
      document.body.classList.toggle('dark-mode', preferences.dark_mode);
    }
    
    if (this.emailNotifToggle) {
      this.emailNotifToggle.checked = preferences.email_notifications;
    }
  }

  async updatePreferences(updates) {
    try {
      const response = await fetch('/api/preferences', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      toastr.success('Preferences updated successfully!');
      return true;
    } catch (error) {
      console.error('Error updating preferences:', error);
      toastr.error('Unable to update preferences. Please try again later.');
      return false;
    }
  }

  setupEventListeners() {
    // Dark mode toggle
    this.darkModeToggle?.addEventListener('change', async (e) => {
      const darkMode = e.target.checked;
      document.body.classList.toggle('dark-mode', darkMode);
      await this.updatePreferences({ dark_mode: darkMode });
    });

    // Email notifications toggle
    this.emailNotifToggle?.addEventListener('change', async (e) => {
      await this.updatePreferences({ email_notifications: e.target.checked });
    });

    // Export functionality
    this.exportButton?.addEventListener('click', () => this.handleExport());
  }

  async handleExport() {
    const startDate = this.startDateInput?.value;
    const endDate = this.endDateInput?.value;
    
    if (!this.validateExportDates(startDate, endDate)) {
      return;
    }

    try {
      const queryParams = new URLSearchParams({
        start_date: startDate,
        end_date: endDate
      });
      
      window.location.href = `/export_stats?${queryParams.toString()}`;
    } catch (error) {
      console.error('Error initiating export:', error);
      toastr.error('Unable to export data. Please try again later.');
    }
  }

  validateExportDates(startDate, endDate) {
    if (!startDate || !endDate) {
      toastr.error('Please select both start and end dates.');
      return false;
    }

    const start = new Date(startDate);
    const end = new Date(endDate);
    
    if (end < start) {
      toastr.error('End date must be after start date.');
      return false;
    }

    const maxRange = 365; // Maximum range in days
    const daysDiff = (end - start) / (1000 * 60 * 60 * 24);
    
    if (daysDiff > maxRange) {
      toastr.error(`Date range cannot exceed ${maxRange} days.`);
      return false;
    }

    return true;
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new UserPreferences();
});
