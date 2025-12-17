# 🎤 Analyse d'Interview IA - Guide Complet

## 📋 Présentation

Application web professionnelle pour transcrire et analyser des interviews avec l'IA. Style LinkedIn pour une présentation élégante des résultats.

### Fonctionnalités
- ✅ Transcription audio (Whisper)
- ✅ Résumé intelligent en 2 paragraphes (T5 + Chunking)
- ✅ Extraction de mots-clés intelligente
- ✅ Analyse d'émotions
- ✅ Interface professionnelle et responsive
- ✅ Favicon et image personnalisables

---

## 🚀 Installation rapide

### 1. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 2. Lancer le serveur
```bash
python api.py
```

Le serveur démarre sur `http://localhost:5050` et ouvre automatiquement votre navigateur.

---

## 📸 Personnalisation des Images

### Favicon (Icône de l'onglet)
1. Remplacez dans `accueil.html` et `analyse.html` (ligne ~8):
```html
<link rel="icon" type="image/png" href="VOTRE_IMAGE_ICI">
```

### Image du Post (Page d'Analyse)
L'espace pour une image est prévu entre le résumé et les mots-clés. 

Pour l'afficher, modifiez le script dans `analyse.html`:
```javascript
const imageUrl = 'votre-url-image.jpg';
document.getElementById('postImage').src = imageUrl;
document.getElementById('imageSection').style.display = 'block';
```

Consultez `IMAGES_GUIDE.md` pour plus de détails.

---

## 🏗️ Architecture

```
AnalyseInterview/
├── api.py                    # Serveur Flask avec modèles IA
├── accueil.html              # Page d'accueil (upload)
├── analyse.html              # Page de résultats (style LinkedIn)
├── script.js                 # Logique frontend
├── style.css                 # Styles des 2 pages
├── transcribe_api.py         # Script original (référence)
├── requirements.txt          # Dépendances Python
├── SETUP.md                  # Ce fichier
├── IMAGES_GUIDE.md           # Guide des images
└── audios/                   # Dossier des fichiers audio

```

---

## 🔧 Configuration

### Port personnalisé
Si 5050 est occupé, modifiez dans `api.py` (dernière ligne):
```python
app.run(debug=True, host='localhost', port=VOTRE_PORT)
```

### Modèles IA
- **Transcription:** OpenAI Whisper (model: "base")
- **Résumé:** plguillou/t5-base-fr-sum-cnndm
- **Stratégie:** Chunking hiérarchique pour les longs textes

---

## 📊 Flux d'utilisation

1. **Page d'accueil** (`/`) - Choisir entre audio ou texte
2. **Upload** - Envoyer le fichier ou coller le texte
3. **Traitement** - API transcrit, résume, extrait mots-clés
4. **Résultats** (`/analyse`) - Page LinkedIn avec:
   - 📝 Résumé en 2 paragraphes
   - 🏷️ Mots-clés comme hashtags
   - 💭 Analyse d'émotions

---

## 💻 Technologies

- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Backend:** Flask, Flask-CORS
- **IA:** OpenAI Whisper, Hugging Face Transformers (T5)
- **Framework de calcul:** PyTorch

---

## 🐛 Dépannage

### "Erreur de connexion avec le serveur"
- Vérifiez que `api.py` est en cours d'exécution
- Vérifiez le port (par défaut 5050)
- Vérifiez que le navigateur accède à `http://localhost:5050`

### Les modèles se téléchargent très lentement
- C'est normal au premier lancement
- Les modèles sont cachés après (~2GB)
- Connexion internet stable recommandée

### Résumé de mauvaise qualité
- Assurez-vous que l'audio est clair
- Texte minimum ~200 caractères recommandé
- Le chunking améliore automatiquement les longs textes

---

## 📝 Notes

- Les résultats sont stockés en localStorage (durée de session)
- Les fichiers audio uploadés sont conservés dans `audios/`
- Pour la production, déployez sur un serveur with HTTPS

---

## 👨‍💻 Support

Pour toute question ou amélioration, consultez les fichiers:
- `IMAGES_GUIDE.md` - Personnalisation des images
- `api.py` - Logique backend
- `style.css` - Styles et design


