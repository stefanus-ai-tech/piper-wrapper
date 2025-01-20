document.addEventListener("DOMContentLoaded", function () {
  const textInput = document.getElementById("text-input");
  const synthesizeBtn = document.getElementById("synthesize-btn");
  const audioPlayer = document.getElementById("audio-player");
  const statusDiv = document.getElementById("status");

  synthesizeBtn.addEventListener("click", async function () {
    const text = textInput.value.trim();

    if (!text) {
      statusDiv.textContent = "Please enter some text to synthesize";
      statusDiv.style.color = "red";
      return;
    }

    statusDiv.textContent = "Synthesizing...";
    statusDiv.style.color = "black";
    synthesizeBtn.disabled = true;

    try {
      const response = await fetch("/synthesize", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text: text }),
      });

      if (!response.ok) {
        throw new Error("Synthesis failed");
      }

      const blob = await response.blob();
      const audioUrl = URL.createObjectURL(blob);

      audioPlayer.src = audioUrl;
      audioPlayer.style.display = "block";
      audioPlayer.play();

      statusDiv.textContent = "Synthesis complete!";
      statusDiv.style.color = "green";
    } catch (error) {
      console.error("Error:", error);
      statusDiv.textContent = "Error during synthesis";
      statusDiv.style.color = "red";
    } finally {
      synthesizeBtn.disabled = false;
    }
  });
});
