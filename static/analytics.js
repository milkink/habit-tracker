// Data passed from the backend
            const chartData = {{ chart_data | tojson }};
            
            // Create a chart using Chart.js
            const ctx = document.getElementById('habitChart').getContext('2d');
            const habitChart = new Chart(ctx, {
                type: 'line', // You can change this to 'bar' if you prefer bar charts
                data: chartData,
                options: {
                    responsive: true,
                    scales: {
                        x: {
                            type: 'category',
                            labels: chartData.labels,
                            title: {
                                display: true,
                                text: 'Days (Last 30 Days)'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Habit Completion Frequency'
                            },
                            beginAtZero: true
                        }
                    }
                }
            });
