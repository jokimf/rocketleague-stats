let a = {
    "type": "bar",
    "data": {
        "title": "Years",
        "labels": ["2018", "2019", "2020", "2021", "2022"],
        "datasets": [{
            "data": [96, 689, 855, 499, 338],
            "label": "Games",
            "borderColor": "rgba(17, 3, 58, 0.8)",
            "borderWidth": 2
        }, {
            "data": [55, 351, 447, 269, 172],
            "label": "Wins",
            "borderColor": "rgba(3, 58, 3, 0.8)",
            "borderWidth": 2
        }, {
            "data": [41, 338, 408, 230, 166],
            "label": "Losses",
            "borderColor": "rgba(58, 3, 3, 0.8)",
            "borderWidth": 2
        }]
    },
    "options": {"x_min": null, "x_max": null, "y_min": null, "y_max": null, "show_legend": true}
}
let url = 'https://jok.im/rlstats_python/data/';
let allCharts = ['datesChart', 'monthChart', 'yearsChart', 'weekdChart'];

for (let i = 0; i < allCharts.length; i++) {
    fetchData("ff").then(data => generateConfig(data)).then(config => {
        new Chart(document.getElementById(allCharts[i]).getContext('2d'), config);
    });
}

async function fetchData(graphName) {
    return await fetch(url + graphName).then(json => json.json());
}

function generateConfig(inputJson) {
    console.log(inputJson)
    let datasets = []
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