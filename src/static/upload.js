document.getElementById("uploadBtn").addEventListener("click", async () => {
    const input = document.getElementById("fileInput");
    const resultTable = document.getElementById("result");

    for (const file of input.files) {
        let formData = new FormData();
        formData.append("file", file);

        const response = await fetch("/rl/uploadreplay", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        let div = document.createElement("div");
        if (data.replay_id) {
            div.innerHTML = `✅ Saved with gameID: ${data.replay_id}`;
        } else {
            if (response.status == 413) {
                div.innerHTML = `❌ Too large to be a replay`
            } else {
                div.innerHTML = `❌ ${data.reason}`;
            }
        }
        let row = resultTable.insertRow();
        let cell = row.insertCell();
        cell.textContent = file.name;
        let cell2 = row.insertCell();
        cell2.textContent = div.textContent;

    }
});