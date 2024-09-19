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