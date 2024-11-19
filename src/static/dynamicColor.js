const tops = document.getElementsByClassName("top_color")
for (let i = 0; i < tops.length; i++) {
    const element = tops[i];
    const value = element.getAttribute("value");
    if (value <= 2) {
        element.style.color = "Orange";
        element.style.fontWeight = "bolder";
    } else if (value <= 10) {
        element.style.color = "SteelBlue";
        element.style.fontWeight = "bolder";
    } else if (value <= 25) {
        element.style.color = "ForestGreen";
    } else if (value <= 50) {
        element.style.color = "LightSlateGrey";
    } else if (value <= 75) {
        element.style.color = "#B6B6B4";
    } else {
        element.style.color = "IndianRed";
    }
}

const statBackgrounds = document.getElementsByClassName("modern");
for (let index = 0; index < statBackgrounds.length; index++) {
    const element = statBackgrounds[index];
    const value = element.getAttribute("value");
    let middleColor;

    if (value <= 2) {
        middleColor = "#FFA500";
    } else if (value <= 10) {
        middleColor = "#4682B4";
    } else if (value <= 25) {
        middleColor = "#228B22";
    } else if (value <= 50) {
        middleColor = "#778899";
    } else if (value <= 75) {
        middleColor = "#B6B6B4";
    } else {
        middleColor = "#CD5C5C";
    }
    //#8d0e0e37
    middleColor += "37";
    element.style.backgroundImage = "linear-gradient(90deg, #161b22 30%," + middleColor + " 45%, #161b22 60%)"
}

const highlightTD = document.getElementsByClassName("highlight_td");
for (let index = 0; index < highlightTD.length; index++) {
    const element = highlightTD[index];

    const value = element.getAttribute("value");
    const columnIndex = element.getAttribute("col");
    let color = element.getAttribute("color");
    const min = element.getAttribute("min");
    const max = element.getAttribute("max");

    if (columnIndex in [1, 2, 3, 10, 16]) {
        continue;
    }

    let backgroundColor;
    if (max - min == 0) {
        backgroundColor = `${color.slice(0, -1)},0)`
    } else {
        opacity = (value - min) / (max - min)
        backgroundColor = color.slice(0, -1) + "," + opacity + ")";
    }

    element.style.backgroundColor = backgroundColor;
}