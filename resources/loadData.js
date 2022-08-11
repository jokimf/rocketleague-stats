let a = {
    "type": "bar", "data": {
        "title": "Dates",
        "labels": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31"],
        "datasets": [{
            "data": [102, 35, 89, 94, 98, 90, 67, 59, 69, 46, 95, 89, 135, 48, 126, 103, 96, 101, 61, 62, 120, 77, 92, 58, 77, 80, 50, 50, 19, 79, 39],
            "borderColor": "rgba(204,255,0,0.8)",
            "borderWidth": 2
        }, {
            "data": [55.88235294117647, 62.857142857142854, 57.30337078651685, 50.0, 54.08163265306123, 55.55555555555556, 41.7910447761194, 40.67796610169492, 46.3768115942029, 54.347826086956516, 53.68421052631579, 48.31460674157304, 56.2962962962963, 54.166666666666664, 52.38095238095239, 56.310679611650485, 51.041666666666664, 51.48514851485149, 39.34426229508197, 54.83870967741935, 56.666666666666664, 50.649350649350644, 51.08695652173913, 50.0, 54.54545454545454, 52.5, 44.0, 48.0, 68.42105263157895, 49.36708860759494, 64.1025641025641],
            "borderColor": "rgba(240,105,173,0.8)",
            "borderWidth": 2
        }, {
            "data": [57, 22, 51, 47, 53, 50, 28, 24, 32, 25, 51, 43, 76, 26, 66, 58, 49, 52, 24, 34, 68, 39, 47, 29, 42, 42, 22, 24, 13, 39, 25],
            "borderColor": "rgba(49,76,35,0.8)",
            "borderWidth": 2
        }, {
            "data": [45, 13, 38, 47, 45, 40, 39, 35, 37, 21, 44, 46, 59, 22, 60, 45, 47, 49, 37, 28, 52, 38, 45, 29, 35, 38, 28, 26, 6, 40, 14],
            "borderColor": "rgba(89,128,173,0.8)",
            "borderWidth": 2
        }]
    }, "options": {"beginAtZero": false, "x_min": 1, "x_max": 2300}
}
//fetch(url).then(res => res.json()).then(out => console.log(out))
let config = {
    type: a.type,
    data: {
        labels: a.data.labels,
        datasets: [{
            label: a.data.datasets[0].label,
            data: a.data.datasets[0].data,
            borderColor: a.data.datasets[0].borderColor,
            borderWidth: 2,
            pointRadius: 0
        }, {
            label: a.data.datasets[1].label,
            data: a.data.datasets[1].data,
            borderColor: a.data.datasets[1].borderColor,
            borderWidth: 2,
            pointRadius: 0
        }, {
            label: a.data.datasets[2].label,
            data: a.data.datasets[2].data,
            borderColor: a.data.datasets[2].borderColor,
            borderWidth: 2,
            pointRadius: 0
        }]
    },
    options: {
        maintainAspectRatio: false,
        responsive: true,
        plugins: {
            title: {
                display: true,
                text: a.data.title
            },
            legend: {
                display: false
            }
        }
        ,
        scales: {
            x: {
                min: a.options.x_min,
                max: a.options.x_max
            },
            y: {
                beginAtZero: a.options.beginAtZero
            }
        }
    },
    plugins: {}
}

const ctx = document.getElementById('myChart').getContext('2d');
const myChart = new Chart(ctx, config);

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