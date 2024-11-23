function createChart(ctx, data, options) {
    return new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            ...options,
            responsive: true,
            maintainAspectRatio: false,
        }
    });
}

// Initialize Analytics Charts
function initializeAnalytics(chartData, streakData) {
    ['daily', 'weekly', 'monthly'].forEach(frequency => {
        // Completion charts
        const completionCtx = document.getElementById(`${frequency}CompletionChart`);
        if (completionCtx) {
            createChart(completionCtx.getContext('2d'), chartData[frequency], {
                plugins: {
                    title: {
                        display: true,
                        text: `${frequency.charAt(0).toUpperCase() + frequency.slice(1)} Habit Completion`
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Completed (1) / Not Completed (0)'
                        },
                        min: 0,
                        max: 1,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            });
        }

        // Streak charts
        const streakCtx = document.getElementById(`${frequency}StreakChart`);
        if (streakCtx) {
            createChart(streakCtx.getContext('2d'), streakData[frequency], {
                plugins: {
                    title: {
                        display: true,
                        text: `${frequency.charAt(0).toUpperCase() + frequency.slice(1)} Habit Streaks`
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Streak Length'
                        },
                        min: 0,
                        beginAtZero: true
                    }
                }
            });
        }
    });
}
