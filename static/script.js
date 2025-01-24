// Function to update generation count
async function updateGenerationCount() {
  try {
    const response = await fetch("/generation-count");
    const data = await response.json();
    document.getElementById("generation-count").textContent = data.count;
  } catch (error) {
    console.error("Error fetching generation count:", error);
  }
}

// Function to update queue position
async function updateQueuePosition() {
  try {
    const response = await fetch("/queue-position");
    const data = await response.json();
    const queueElement = document.getElementById("queue-position");
    queueElement.textContent = data.position;
    if (data.position > 0) {
      queueElement.parentElement.style.display = "block";
    } else {
      queueElement.parentElement.style.display = "none";
    }
  } catch (error) {
    console.error("Error fetching queue position:", error);
  }
}

document.addEventListener("DOMContentLoaded", function () {
  // Update generation count on page load
  updateGenerationCount();
  const textInput = document.getElementById("text-input");
  const synthesizeBtn = document.getElementById("synthesize-btn");
  const audioPlayer = document.getElementById("audio-player");
  const statusDiv = document.getElementById("status");
  const voiceSelect = document.getElementById("voice-select");
  const loadingContainer = document.getElementById("loading-container");
  const timeTakenDiv = document.getElementById("time-taken");
  const charCounter = document.querySelector('.char-counter');
  const charCount = document.getElementById('char-count');

  // Character limit
  const CHAR_LIMIT = 1024;
  const WARNING_THRESHOLD = 800;

  // Update character counter
  function updateCharCounter() {
    const length = textInput.value.length;
    charCount.textContent = length;
    const charAlert = document.getElementById('char-alert');

    // Update counter styling and alerts
    if (length >= CHAR_LIMIT) {
      charCounter.classList.add('error');
      charAlert.style.display = 'block';
      synthesizeBtn.disabled = true;
      synthesizeBtn.classList.add('disabled');
      if (length === CHAR_LIMIT) alert('Character limit reached!');
    } else if (length >= WARNING_THRESHOLD) {
      charCounter.classList.add('warning');
      charAlert.style.display = 'none';
      synthesizeBtn.disabled = false;
      synthesizeBtn.classList.remove('disabled');
    } else {
      charCounter.classList.remove('warning', 'error');
      charAlert.style.display = 'none';
      synthesizeBtn.disabled = false;
      synthesizeBtn.classList.remove('disabled');
    }
  }

  // Initialize character counter
  updateCharCounter();
  textInput.addEventListener('input', updateCharCounter);

  let startTime;
  let timeTakenInterval;

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

    // Reset loading state and timing
    startTime = Date.now();
    loadingContainer.style.display = "flex";
    timeTakenDiv.style.display = "none";
    statusDiv.textContent = "Synthesizing...";
    statusDiv.style.color = "black";
    synthesizeBtn.disabled = true;

    // Update time taken every second
    timeTakenInterval = setInterval(() => {
      const seconds = Math.floor((Date.now() - startTime) / 1000);
      timeTakenDiv.textContent = `Processing: ${seconds}s`;
    }, 1000);

    try {
      const response = await fetch("/synthesize", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: text,
          voiceId: selectedVoiceId,
        }),
      });

      if (!response.ok) throw new Error("Synthesis failed");

      const blob = await response.blob();
      const audioUrl = URL.createObjectURL(blob);

      audioPlayer.src = audioUrl;
      audioPlayer.style.display = "block";
      audioPlayer.play();

      statusDiv.textContent = "Synthesis complete!";
      statusDiv.style.color = "green";
      
      // Update generation count after successful synthesis
      updateGenerationCount();
    } catch (error) {
      console.error("Error:", error);
      statusDiv.textContent = "Error during synthesis";
      statusDiv.style.color = "red";
    } finally {
      clearInterval(timeTakenInterval);
      loadingContainer.style.display = "none";
      synthesizeBtn.disabled = false;

      // Show final time taken
      const endTime = Date.now();
      const duration = (endTime - startTime) / 1000;
      timeTakenDiv.style.display = "block";
      timeTakenDiv.textContent = `Generated in ${duration.toFixed(2)} seconds`;
    }
  });
});
