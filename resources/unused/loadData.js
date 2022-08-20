let allCharts = ["datesChart", "monthChart", "yearsChart", "weekdChart", "grief", "wins_last_20", "winrate", "solo_goals",
    "performance_score", "performance_goals", "performance_assists", "performance_saves", "performance_shots", "performance_share_score", "performance_share_goals",
    "performance_share_assists", "performance_share_saves", "performance_share_shots", "cumulative_stats_score", "cumulative_stats_goals", "cumulative_stats_assists",
    "cumulative_stats_saves", "cumulative_stats_shots", "mvp_lvp_score"];

for (let i = 0; i < allCharts.length; i++) {
    fetchData(allCharts[i]).then(data => generateConfig(data)).then(config => {
        new Chart(document.getElementById(allCharts[i]).getContext('2d'), config);
    });
}

async function fetchData(graphName) {
    return await fetch('https://jok.im/rlstats_python/data/' + graphName).then(json => json.json());
}

function generateConfig(inputJson) {
    let datasets = [];
    for (let i = 0; i < inputJson.data.datasets.length; i++) {
        datasets.push({
            label: inputJson.data.datasets[i].label,
            data: inputJson.data.datasets[i].data,
            borderColor: inputJson.data.datasets[i].borderColor,
            borderWidth: 4,
            pointRadius: 0
        })
    }
    return {
        type: inputJson.type,
        data: {
            labels: inputJson.data.labels,
            datasets: datasets
        },
        options: {
            maintainAspectRatio: false,
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: inputJson.data.title
                },
                legend: {
                    display: inputJson.options.show_legend
                }
            },
            scales: {
                x: {
                    min: inputJson.options.x_min,
                    max: inputJson.options.x_max
                },
                y: {
                    min: inputJson.options.y_min,
                    max: inputJson.options.y_max
                }
            }
        },
        plugins: {}
    }
}

function changeX() {
    p(myChart);
}

function p(chart) {
    //chart.options.plugins.title.text = 'new title';
    let xmin = chart.scales.x.min
    let xmax = chart.scales.x.max
    chart.options.scales.x.min = xmin + 100;
    chart.update();
}