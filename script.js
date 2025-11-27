// script.js

document.getElementById("uploadForm").addEventListener("submit", async function(e) {
  e.preventDefault();
  const fileInput = document.getElementById("videoInput");
  const errorMessage = document.getElementById("errorMessage");
  const transcriptionDiv = document.getElementById("transcriptionResult");

  errorMessage.textContent = "";
  transcriptionDiv.textContent = "";

  if (!fileInput.files.length) {
    errorMessage.textContent = "⚠️ Veuillez sélectionner un fichier audio (.mp3) pour continuer.";
    return;
  }

  const formData = new FormData();
  formData.append('audio', fileInput.files[0]);

  try {
    const response = await fetch('http://localhost:5000/transcribe', {
      method: 'POST',
      body: formData
    });
    const data = await response.json();
    if (data.transcription) {
      transcriptionDiv.textContent = data.transcription;
    } else if (data.error) {
      errorMessage.textContent = data.error;
    } else {
      errorMessage.textContent = "Erreur lors de la transcription.";
    }
  } catch (err) {
    errorMessage.textContent = "Erreur lors de la communication avec le serveur.";
  }
});
