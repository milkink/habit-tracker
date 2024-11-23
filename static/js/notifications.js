// Notification functions
function loadNotifications() {
    $.ajax({
        url: '/notifications',
        type: 'GET',
        success: function(notifications) {
            const container = $('#notifications-container');
            container.empty();

            if (notifications.length === 0) {
                container.append('<p>No new notifications.</p>');
            } else {
                notifications.forEach(notification => {
                    container.append('<p>' + notification.message + '</p>');
                });
            }
        },
        error: function() {
            $('#notifications-container').html('<p>Error loading notifications.</p>');
        }
    });
}
