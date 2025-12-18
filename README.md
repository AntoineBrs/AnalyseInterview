# 🎤 Analyse d'Interview IA - Guide Complet

## 📋 Présentation

Application web professionnelle pour transcrire et analyser des interviews avec l'IA. Style LinkedIn pour une présentation élégante des résultats.

### Fonctionnalités
- ✅ Transcription audio (Whisper)
- ✅ Résumé intelligent (T5 + Chunking)
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
├── README.md                  # Ce fichier                

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
   - 📝 Résumé 
   - 🏷️ Mots-clés avec hashtags
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
- `api.py` - Logique backend
- `style.css` - Styles et design


