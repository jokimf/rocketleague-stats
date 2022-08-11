let a = {
    "type": "bar",
    "data": {
        "title": "PFFFFFFFFFFFD",
        "labels": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
        "datasets": [{
            "label": "Knus",
            "data": [23, 61, 11, 34, 66],
            "borderColor": "rgba(47,147,26,0.8)",
            "borderWidth": 3
        }, {
            "label": "Puad",
            "data": [4, 33, 21, 40, 10],
            "borderColor": "rgba(147,26,26,0.8)",
            "borderWidth": 3
        }, {"label": "Sticker", "data": [55, 44, 22, 30, 10], "borderColor": "rgba(26,115,147,0.8)", "borderWidth": 3}]
    },
    "options": {"beginAtZero": true}
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
            borderWidth: 2
        }, {
            label: a.data.datasets[1].label,
            data: a.data.datasets[1].data,
            borderColor: a.data.datasets[1].borderColor,
            borderWidth: 2
        }, {
            label: a.data.datasets[2].label,
            data: a.data.datasets[2].data,
            borderColor: a.data.datasets[2].borderColor,
            borderWidth: 2
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
            y: {
                beginAtZero: a.options.beginAtZero
            }
        }
    },
    plugins: {}
}
const ctx = document.getElementById('myChart').getContext('2d');
const myChart = new Chart(ctx, config);