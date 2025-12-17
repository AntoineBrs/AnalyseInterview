// script.js

// --- Gestion du menu burger ---
const menuTrigger = document.getElementById('menuTrigger');
const menuDropdown = document.getElementById('menuDropdown');

if (menuTrigger) {
  menuTrigger.addEventListener('click', function(e) {
    e.preventDefault();
    this.classList.toggle('active');
    menuDropdown.classList.toggle('active');
  });

  // Fermer le menu quand on clique ailleurs
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.menu-burger')) {
      menuTrigger.classList.remove('active');
      menuDropdown.classList.remove('active');
    }
  });

  // Gestion des clics sur les items du menu
  document.querySelectorAll('.menu-item').forEach(item => {
    item.addEventListener('click', function(e) {
      e.preventDefault();
      const action = this.getAttribute('data-action');
      
      menuTrigger.classList.remove('active');
      menuDropdown.classList.remove('active');
      
      switch(action) {
        case 'history':
          alert('📚 Historique\n\nFonctionnalité à venir:\n- Voir toutes les interviews analysées\n- Reprendre une analyse antérieure\n- Gérer l\'historique');
          break;
        case 'import':
          alert('📥 Importer les données\n\nFonctionnalité à venir:\n- Importer des résultats JSON\n- Charger des interviews depuis un fichier');
          break;
        case 'settings':
          alert('⚙️ Paramètres\n\nFonctionnalité à venir:\n- Paramètres de transcription\n- Paramètres de résumé\n- Préférences d\'interface');
          break;
        case 'about':
          document.getElementById('aboutModal').classList.add('show');
          break;
        case 'help':
          document.getElementById('helpModal').classList.add('show');
          break;
      }
    });
  });
}

// Gestion des modals
const modals = document.querySelectorAll('.modal');
modals.forEach(modal => {
  // Fermer en cliquant le X
  const closeBtn = modal.querySelector('.modal-close');
  if (closeBtn) {
    closeBtn.addEventListener('click', function() {
      modal.classList.remove('show');
    });
  }

  // Fermer en cliquant en dehors du contenu
  modal.addEventListener('click', function(e) {
    if (e.target === this) {
      this.classList.remove('show');
    }
  });
});

// --- Gestion des onglets ---
document.querySelectorAll('.accueil-tab-button').forEach(button => {
  button.addEventListener('click', function(e) {
    e.preventDefault();
    const tabName = this.getAttribute('data-tab');
    
    // Désactiver tous les onglets
    document.querySelectorAll('.accueil-tab-button').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.accueil-tab-content').forEach(tab => tab.classList.remove('active'));
    
    // Activer l'onglet sélectionné
    this.classList.add('active');
    document.getElementById(tabName + '-tab').classList.add('active');
  });
});

// --- Traitement du formulaire ---
document.getElementById("uploadForm").addEventListener("submit", async function(e) {
  e.preventDefault();
  
  const errorMessage = document.getElementById("errorMessage");
  const loadingMessage = document.getElementById("loadingMessage");
  const audioInput = document.getElementById("audioInput");
  const textInput = document.getElementById("textInput");

  errorMessage.textContent = "";
  loadingMessage.style.display = "none";

  // Déterminer quel onglet est actif
  const activeTab = document.querySelector('.accueil-tab-button.active').getAttribute('data-tab');
  const formData = new FormData();

  if (activeTab === 'audio') {
    if (!audioInput.files.length) {
      errorMessage.textContent = "⚠️ Veuillez sélectionner un fichier audio (.mp3) pour continuer.";
      return;
    }
    formData.append('audio', audioInput.files[0]);
  } else if (activeTab === 'text') {
    if (!textInput.value.trim()) {
      errorMessage.textContent = "⚠️ Veuillez entrer un texte pour continuer.";
      return;
    }
    formData.append('text', textInput.value.trim());
  }

  try {
    loadingMessage.style.display = "flex";
    
    const response = await fetch('http://localhost:5050/transcribe', {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    loadingMessage.style.display = "none";
    
    if (response.ok && data.summary) {
      // Stocker les données dans localStorage
      localStorage.setItem('summary', JSON.stringify(data.summary));
      localStorage.setItem('keywords', JSON.stringify(data.keywords));
      localStorage.setItem('sentiments', data.sentiments);
      localStorage.setItem('transcription', data.transcription);
      
      // Rediriger vers la page d'analyse
      window.location.href = '/analyse';
    } else if (data.error) {
      errorMessage.textContent = "❌ " + data.error;
    } else {
      errorMessage.textContent = "❌ Erreur lors du traitement.";
    }
  } catch (err) {
    loadingMessage.style.display = "none";
    errorMessage.textContent = "❌ Erreur de connexion avec le serveur. Assurez-vous que l'API est en cours d'exécution.";
    console.error(err);
  }
});
