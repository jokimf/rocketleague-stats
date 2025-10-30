document.getElementById("uploadBtn").addEventListener("click", async () => {
    const input = document.getElementById("fileInput");
    const resultDiv = document.getElementById("result");
    resultDiv.innerHTML = "Uploading...";

    const formData = new FormData();
    for (const file of input.files) {
        formData.append("files", file);
    }

    try {
        const response = await fetch("/rl/uploadreplay", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (data.valid) {
            resultDiv.innerHTML = `<p style="color: green;">✅ All files valid!</p>`;
        } else {
            resultDiv.innerHTML = `<p style="color: red;">❌ Some files invalid:</p><ul>${data.invalid.map(f => `<li>${f}</li>`).join("")}</ul>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
});