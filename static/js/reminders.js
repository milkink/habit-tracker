document.addEventListener('DOMContentLoaded', () => {
  const reminderForm = document.getElementById('reminder-form');
  const remindersContainer = document.querySelector('.reminders-container');

  const fetchReminders = async () => {
    try {
      const response = await fetch('/reminders');
      const reminders = await response.json();
      
      remindersContainer.innerHTML = reminders.map(reminder => `
        <div class="reminder-card shadow-sm p-3 mb-3 bg-white rounded">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <h5 class="mb-1">${reminder.habit_name}</h5>
              <p class="mb-1">Time: ${reminder.time}</p>
              <p class="mb-1">Days: ${reminder.days.join(', ')}</p>
            </div>
            <div class="form-check form-switch">
              <input class="form-check-input" type="checkbox" 
                     data-id="${reminder.id}" 
                     ${reminder.enabled ? 'checked' : ''}
                     onchange="toggleReminder(${reminder.id}, this.checked)">
            </div>
          </div>
        </div>
      `).join('');
    } catch (error) {
      console.error('Error fetching reminders:', error);
    }
  };

  reminderForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(reminderForm);
    const reminderData = {
      habit_id: formData.get('habit_id'),
      time: formData.get('time'),
      days: Array.from(formData.getAll('days'))
    };

    try {
      const response = await fetch('/reminders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(reminderData)
      });
      
      if (response.ok) {
        await fetchReminders();
        reminderForm.reset();
        toastr.success('Reminder set successfully!');
      }
    } catch (error) {
      console.error('Error creating reminder:', error);
      toastr.error('Error setting reminder.');
    }
  });

  window.toggleReminder = async (reminderId, enabled) => {
    try {
      await fetch(`/reminders/${reminderId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ enabled })
      });
      toastr.success('Reminder updated successfully!');
    } catch (error) {
      console.error('Error toggling reminder:', error);
      toastr.error('Error updating reminder.');
    }
  };

  // Initial load of reminders
  fetchReminders();
});
