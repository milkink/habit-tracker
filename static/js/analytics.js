// Analytics Chart Creation
function createChart(ctx, data, options) {
    if (!data || !data.labels || !data.values) {
        console.error('Invalid data format:', data);
        return null;
    }

    const chartConfig = {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: data.label || '',
                data: data.values,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            ...options,
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            }
        }
    };

    try {
        return new Chart(ctx, chartConfig);
    } catch (error) {
        console.error('Error creating chart:', error);
        return null;
    }
}

// Initialize Analytics Charts
function initializeAnalytics(chartData, streakData) {
    console.log('Chart Data:', chartData);
    console.log('Streak Data:', streakData);

    if (!chartData || !streakData) {
        console.error('Missing data for charts');
        return;
    }

    ['daily', 'weekly', 'monthly'].forEach(frequency => {
        // Completion charts
        const completionCtx = document.getElementById(`${frequency}CompletionChart`);
        if (completionCtx && chartData[frequency]) {
            console.log(`Creating ${frequency} completion chart`);
            createChart(completionCtx, chartData[frequency], {
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        ticks: {
                            stepSize: 1,
                            callback: value => value === 1 ? 'Completed' : 'Not Completed'
                        }
                    }
                }
            });
        }

        // Streak charts
        const streakCtx = document.getElementById(`${frequency}StreakChart`);
        if (streakCtx && streakData[frequency]) {
            console.log(`Creating ${frequency} streak chart`);
            createChart(streakCtx, streakData[frequency], {
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            });
        }
    });
}

// Wait for DOM and data
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded');
    // Add a small delay to ensure data is loaded
    setTimeout(() => {
        if (typeof chartData !== 'undefined' && typeof streakData !== 'undefined') {
            initializeAnalytics(chartData, streakData);
        } else {
            console.error('Chart data or streak data is undefined');
        }
    }, 100);
});
