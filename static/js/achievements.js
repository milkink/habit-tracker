// Achievement functions
function loadAchievements() {
    $.get('/achievements', function(achievements) {
        const container = $('#achievements-container');
        container.empty();
        
        achievements.forEach(achievement => {
            container.append(`
                <div class="col-md-3 mb-3">
                    <div class="card achievement-card">
                        <div class="card-body text-center">
                            <i class="fas ${achievement.badge_icon} fa-2x mb-2"></i>
                            <h5 class="card-title">${achievement.name}</h5>
                            <p class="card-text">${achievement.description}</p>
                            <small class="text-muted">Earned: ${achievement.earned_date}</small>
                        </div>
                    </div>
                </div>
            `);
        });
    });
}
