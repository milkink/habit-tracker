function createGradient(ctx, color) {
    try {
        // Parse the color components
        const rgb = color.split(',').map(num => parseInt(num.trim(), 10));
        if (rgb.length !== 3 || rgb.some(isNaN)) {
            throw new Error('Invalid color format');
        }

        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, 0.4)`);
        gradient.addColorStop(1, `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, 0.0)`);
        return gradient;
    } catch (error) {
        console.error('Error creating gradient:', error);
        return 'rgba(75, 192, 192, 0.2)'; // Fallback color
    }
}

function generateRandomColor() {
    const hue = Math.floor(Math.random() * 360);
    const saturation = 70 + Math.random() * 10; // 70-80%
    const lightness = 45 + Math.random() * 10; // 45-55%
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

function hslToRgb(hsl) {
    // Extract HSL values using regex
    const match = hsl.match(/hsl\((\d+),\s*(\d+)%,\s*(\d+)%\)/);
    if (!match) return [75, 192, 192]; // Fallback color

    let [, h, s, l] = match.map(Number);
    s /= 100;
    l /= 100;

    const c = (1 - Math.abs(2 * l - 1)) * s;
    const x = c * (1 - Math.abs((h / 60) % 2 - 1));
    const m = l - c / 2;
    let r = 0, g = 0, b = 0;

    if (0 <= h && h < 60) {
        [r, g, b] = [c, x, 0];
    } else if (60 <= h && h < 120) {
        [r, g, b] = [x, c, 0];
    } else if (120 <= h && h < 180) {
        [r, g, b] = [0, c, x];
    } else if (180 <= h && h < 240) {
        [r, g, b] = [0, x, c];
    } else if (240 <= h && h < 300) {
        [r, g, b] = [x, 0, c];
    } else if (300 <= h && h < 360) {
        [r, g, b] = [c, 0, x];
    }

    return [
        Math.round((r + m) * 255),
        Math.round((g + m) * 255),
        Math.round((b + m) * 255)
    ];
}

function createChart(ctx, data, options) {
    if (!ctx || !data || !options) {
        console.error('Missing required parameters for chart creation');
        return null;
    }

    try {
        const context = ctx.getContext('2d');
        if (!context) {
            console.error('Could not get 2d context');
            return null;
        }

        // Enhance datasets with better styling
        data.datasets = data.datasets.map(dataset => {
            // Generate a unique color for each dataset if not provided
            const color = dataset.borderColor || generateRandomColor();
            const rgb = hslToRgb(color);

            return {
                ...dataset,
                borderColor: `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`,
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                backgroundColor: createGradient(context, rgb.join(',')),
                pointBackgroundColor: `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointHoverBorderWidth: 3,
                pointHoverBackgroundColor: `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`,
                pointHoverBorderColor: '#fff'
            };
        });

        return new Chart(context, {
            type: 'line',
            data: data,
            options: {
                ...options,
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    ...options.plugins,
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                            font: {
                                size: 13,
                                family: "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif"
                            }
                        }
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(255, 255, 255, 0.9)',
                        titleColor: '#333',
                        bodyColor: '#666',
                        borderColor: '#ddd',
                        borderWidth: 1,
                        padding: 12,
                        boxPadding: 6,
                        usePointStyle: true,
                        callbacks: {
                            label: function(context) {
                                return ` ${context.dataset.label}: ${context.parsed.y}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                size: 12
                            },
                            maxRotation: 45,
                            minRotation: 45
                        }
                    },
                    y: {
                        display: true,
                        grid: {
                            borderDash: [8, 4],
                            color: '#e0e0e0'
                        },
                        ticks: {
                            font: {
                                size: 12
                            },
                            padding: 10
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error creating chart:', error);
        return null;
    }
}

function initializeAnalytics(chartData, streakData) {
    if (!chartData || !streakData) {
        console.error('Chart data is missing');
        return;
    }

    ['daily', 'weekly', 'monthly'].forEach(frequency => {
        try {
            // Completion charts
            const completionCtx = document.getElementById(`${frequency}CompletionChart`);
            if (completionCtx && chartData[frequency]) {
                createChart(completionCtx, chartData[frequency], {
                    plugins: {
                        title: {
                            display: true,
                            text: `${frequency.charAt(0).toUpperCase() + frequency.slice(1)} Habit Completion`,
                            font: {
                                size: 16,
                                weight: 'bold',
                                family: "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif"
                            },
                            padding: 20
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Date',
                                font: {
                                    weight: 'bold'
                                }
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Completed (1) / Not Completed (0)',
                                font: {
                                    weight: 'bold'
                                }
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
            if (streakCtx && streakData[frequency]) {
                createChart(streakCtx, streakData[frequency], {
                    plugins: {
                        title: {
                            display: true,
                            text: `${frequency.charAt(0).toUpperCase() + frequency.slice(1)} Habit Streaks`,
                            font: {
                                size: 16,
                                weight: 'bold',
                                family: "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif"
                            },
                            padding: 20
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Date',
                                font: {
                                    weight: 'bold'
                                }
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Streak Length',
                                font: {
                                    weight: 'bold'
                                }
                            },
                            min: 0,
                            beginAtZero: true
                        }
                    }
                });
            }
        } catch (error) {
            console.error(`Error initializing ${frequency} charts:`, error);
        }
    });
}
