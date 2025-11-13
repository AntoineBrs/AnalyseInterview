document.getElementById("uploadForm").addEventListener("submit", function (e) {
  e.preventDefault();

  const fileInput = document.getElementById("videoInput");
  const errorMessage = document.getElementById("errorMessage");

  errorMessage.textContent = "";
  
  if (!fileInput.files.length) {
    errorMessage.textContent = "⚠️ Veuillez sélectionner une vidéo ou un fichier texte pour continuer.";
    return;
  }

  const file = fileInput.files[0];
  console.log("Fichier sélectionné :", file.name);

  localStorage.setItem("summary", JSON.stringify([
    "Le candidat présente son parcours professionnel.",
    "Il met en avant ses compétences en communication.",
    "Il souligne son esprit d’équipe et sa motivation.",
    "Il évoque ses expériences passées et réussites.",
    "Il conclut sur ses objectifs futurs."
  ]));
  
  localStorage.setItem("keywords", "motivation, travail d’équipe, communication, ambition, expérience");
  localStorage.setItem("sentiments", "Analyse émotionnelle : Positif à 92% 😊");

  
  window.location.href = "result.html";
});
