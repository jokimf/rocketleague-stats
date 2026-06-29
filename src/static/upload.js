document.getElementById("uploadBtn").addEventListener("click", async () => {
    const input = document.getElementById("fileInput");
    const resultTable = document.getElementById("result");

    if (!input.files.length) return;

    const uploadPromises = Array.from(input.files).map(async (file) => {
        let formData = new FormData();
        formData.append("replay_file", file);

        let row = resultTable.insertRow();
        let cellName = row.insertCell();
        let cellStatus = row.insertCell();
        cellName.textContent = file.name;
        cellStatus.textContent = "⏳ Uploading...";

        try {
            const response = await fetch("/rl/uploadreplay", {
                method: "POST",
                body: formData,
            });
            if (response.status === 413) {
                cellStatus.textContent = "❌ Too large to be a replay";
                return;
            }
            if (!response.ok) {
                cellStatus.textContent = `❌ Server Error (${response.status})`;
                return;
            }
            const data = await response.json();

            if (data.replay_id) {
                cellStatus.textContent = `✅ Saved with gameID: ${data.replay_id}`;
            } else {
                cellStatus.textContent = `❌ ${data.reason || "Unknown error"}`;
            }

        } catch (error) {
            cellStatus.textContent = "❌ Network error occurred";
            console.error("Upload failed:", error);
        }
    });
    await Promise.all(uploadPromises);
});