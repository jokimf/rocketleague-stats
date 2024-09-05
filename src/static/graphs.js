fetch("/rl/data")
  .then(response => response.json())
  .then(data => {
    new Chart(document.getElementById('myChart'), data);
  })

