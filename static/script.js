document.addEventListener("DOMContentLoaded", function () {
  const textInput = document.getElementById("text-input");
  const synthesizeBtn = document.getElementById("synthesize-btn");
  const audioPlayer = document.getElementById("audio-player");
  const statusDiv = document.getElementById("status");
  const voiceSelect = document.getElementById("voice-select");

  // Fetch available voices from the server
  async function fetchVoices() {
    try {
      const response = await fetch("/voices");
      const voices = await response.json();
      populateVoiceSelect(voices);
    } catch (error) {
      console.error("Error fetching voices:", error);
    }
  }

  // Populate Voice Select
  function populateVoiceSelect(voices) {
    voices.forEach((voice) => {
      const option = document.createElement("option");
      option.value = voice.id;
      option.textContent = `${voice.language} - ${voice.name} (${voice.quality})`;
      voiceSelect.appendChild(option);
    });
  }

  fetchVoices(); // Call the function to fetch and populate the dropdown

  synthesizeBtn.addEventListener("click", async function () {
    const text = textInput.value.trim();
    const selectedVoiceId = voiceSelect.value;

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
        body: JSON.stringify({
          text: text,
          voiceId: selectedVoiceId, // Pass the selected voice ID
        }),
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
