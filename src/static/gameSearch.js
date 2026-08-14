document.getElementById('search-button').addEventListener('click', () => {
    const minVal = Number(document.getElementById('from').value);
    const maxVal = Number(document.getElementById('to').value);
    if (minVal === '' || maxVal === '') {
        alert('Fill out both number inputs.');
        return;
    }
    if (minVal > maxVal) {
        let temp = minVal;
        minVal = maxVal;
        maxVal = temp;
    }
    window.location.href = `/rl/games?${new URLSearchParams({
        minID: minVal,
        maxID: maxVal
    }).toString()}`;
});