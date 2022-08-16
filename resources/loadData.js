let a ={"type": "bar", "data": {"title": "Dates", "labels": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31"], "datasets": [{"data": [102, 35, 89, 94, 98, 90, 67, 59, 69, 46, 95, 89, 135, 48, 126, 103, 96, 101, 61, 62, 120, 77, 92, 58, 77, 80, 50, 50, 19, 79, 39], "label": "Games", "borderColor": "rgba(17, 3, 58, 0.8)", "borderWidth": 2}, {"data": [57, 22, 51, 47, 53, 50, 28, 24, 32, 25, 51, 43, 76, 26, 66, 58, 49, 52, 24, 34, 68, 39, 47, 29, 42, 42, 22, 24, 13, 39, 25], "label": "Wins", "borderColor": "rgba(3, 58, 3, 0.8)", "borderWidth": 2}, {"data": [45, 13, 38, 47, 45, 40, 39, 35, 37, 21, 44, 46, 59, 22, 60, 45, 47, 49, 37, 28, 52, 38, 45, 29, 35, 38, 28, 26, 6, 40, 14], "label": "Losses", "borderColor": "rgba(58, 3, 3, 0.8)", "borderWidth": 2}]}, "options": {"x_min": null, "x_max": null, "y_min": null, "y_max": null, "show_legend": true}}
let url = 'https://jok.im/rlstats_python/data/pfd'
//let b = fetch(url).then(res => res.json()).then(out => console.log(out)) // doesn't work yet because CORS

const datesChart = new Chart(document.getElementById('datesChart').getContext('2d'), generateConfig(a));
const monthChart = new Chart(document.getElementById('monthChart').getContext('2d'), generateConfig(a));
const yearsChart = new Chart(document.getElementById('yearsChart').getContext('2d'), generateConfig(a));
const weekdChart = new Chart(document.getElementById('weekdChart').getContext('2d'), generateConfig(a));

function generateConfig(inputJson) {
    let datasets = []
    for (let i = 0; i < a.data.datasets.length; i++) {
        datasets.push({
                label: a.data.datasets[i].label,
                data: a.data.datasets[i].data,
                borderColor: a.data.datasets[i].borderColor,
                borderWidth: 4,
                pointRadius: 0
            })
    }
    let blank = {
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
    return blank
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