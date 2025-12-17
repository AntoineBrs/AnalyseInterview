from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import whisper
from transformers import T5Tokenizer, T5ForConditionalGeneration
import json
import re
import webbrowser
import threading
import time

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# --- Charger les modèles ---
print("Chargement des modèles...")
whisper_model = whisper.load_model("base")

t5_model_name = "plguillou/t5-base-fr-sum-cnndm"
tokenizer = T5Tokenizer.from_pretrained(t5_model_name)
t5_model = T5ForConditionalGeneration.from_pretrained(t5_model_name)
print("Modèles chargés ✓")

# --- Fonction pour découper le texte en chunks ---
def chunk_text(text, chunk_size=500, overlap=50):
    """
    Divise le texte en chunks avec chevauchement
    chunk_size: nombre de mots par chunk
    overlap: nombre de mots chevauchés entre chunks
    """
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence_words = len(sentence.split())
        current_size += sentence_words
        current_chunk.append(sentence)
        
        if current_size >= chunk_size:
            chunk_text = ' '.join(current_chunk)
            if chunk_text.strip():
                chunks.append(chunk_text)
            current_size = 0
            current_chunk = []
    
    # Ajouter le dernier chunk
    if current_chunk:
        chunk_text = ' '.join(current_chunk)
        if chunk_text.strip():
            chunks.append(chunk_text)
    
    return chunks

# --- Fonction de résumé améliorée avec chunking ---
def summarize_with_t5(text, max_input_tokens=1024, max_output_tokens=150, min_output_tokens=80):
    """
    Résume le texte en utilisant un chunking hierarchique
    """
    # Si le texte est court, résumer directement
    text_length = len(text.split())
    if text_length < 300:
        input_text = "summarize: " + text
        inputs = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=max_input_tokens)
        summary_ids = t5_model.generate(
            inputs["input_ids"],
            max_length=max_output_tokens,   
            min_length=min_output_tokens,    
            length_penalty=2.0,              
            num_beams=4,                     
            no_repeat_ngram_size=2,
            early_stopping=True,
            do_sample=False
        )
        return tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    
    # Pour les textes longs, utiliser un chunking hierarchique
    chunks = chunk_text(text, chunk_size=400, overlap=50)
    chunk_summaries = []
    
    print(f"Traitement de {len(chunks)} chunks...")
    
    for i, chunk in enumerate(chunks):
        if chunk.strip():
            input_text = "summarize: " + chunk
            inputs = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=max_input_tokens)
            
            summary_ids = t5_model.generate(
                inputs["input_ids"],
                max_length=max_output_tokens,   
                min_length=min_output_tokens,    
                length_penalty=1.5,              
                num_beams=4,                     
                no_repeat_ngram_size=2,
                early_stopping=True,
                do_sample=False
            )
            summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            chunk_summaries.append(summary)
    
    # Combiner les résumés des chunks et en faire un résumé final
    combined_summary = " ".join(chunk_summaries)
    
    if len(combined_summary.split()) > 300:
        input_text = "summarize: " + combined_summary
        inputs = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=max_input_tokens)
        
        summary_ids = t5_model.generate(
            inputs["input_ids"],
            max_length=max_output_tokens * 2,   
            min_length=min_output_tokens * 1.5,    
            length_penalty=2.0,              
            num_beams=8,                     
            no_repeat_ngram_size=3,
            early_stopping=True,
            do_sample=False
        )
        final_summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    else:
        final_summary = combined_summary
    
    return final_summary

# --- Fonction pour extraire mots-clés intelligemment ---
def extract_keywords(text):
    """
    Extrait les mots-clés importants du RÉSUMÉ (plus propre que la transcription)
    Filtre: Noms, Acronymes, Adjectifs qualificatifs, Verbes à l'infinitif
    EXCLUT: adverbes, conjonctions, pronoms, quantificateurs, mots vagues
    """
    from collections import Counter
    import re
    
    # Stopwords français complets (en minuscule)
    stopwords_fr = {
        'le', 'la', 'les', 'de', 'du', 'un', 'une', 'des', 'et', 'ou', 'mais', 
        'donc', 'car', 'pour', 'par', 'dans', 'en', 'à', 'avec', 'sans', 'sur', 
        'sous', 'entre', 'parmi', 'durant', 'pendant', 'avant', 'après', 'est', 
        'être', 'avoir', 'que', 'qui', 'où', 'quand', 'comment', 'pourquoi', 'ça',
        'c\'est', 'c', 'pas', 'va', 'vais', 'vous', 'nous', 'je', 'tu', 'il', 'elle',
        'on', 'ce', 'cet', 'cette', 'ces', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes',
        'son', 'sa', 'ses', 'notre', 'nos', 'votre', 'vos', 'leur', 'leurs',
        'aujourd', 'aujourd\'hui', 'demain', 'hier', 'là', 'ici'
    }
    
    # Pronoms à exclure explicitement
    pronouns = {
        'il', 'elle', 'on', 'nous', 'vous', 'je', 'tu', 'me', 'te', 'se',
        'moi', 'toi', 'lui', 'eux', 'elles', 'celui', 'celle', 'ceux', 'celles'
    }
    
    # Adverbes et quantificateurs à exclure
    adverbs_quantifiers = {
        'beaucoup', 'très', 'peu', 'plus', 'moins', 'aussi', 'encore', 'alors',
        'bien', 'mal', 'mieux', 'pire', 'seulement', 'même', 'presque', 'très',
        'trop', 'assez', 'environ', 'environ', 'peut-être', 'sans', 'avec',
        'vite', 'lentement', 'souvent', 'jamais', 'toujours', 'parfois'
    }
    
    # Adverbes terminant en -ment
    adverbs_endings = ('ment', 'amment', 'emment', 'ément')
    
    # Conjonctions à exclure
    conjunctions = {
        'et', 'ou', 'mais', 'donc', 'car', 'ni', 'cependant', 'toutefois',
        'puisque', 'parce', 'lorsque', 'tandis', 'd\'ailleurs', 'moreover'
    }
    
    # Mots vagues et génériques à exclure
    vague_words = {
        'manière', 'façon', 'sorte', 'type', 'genre', 'cas', 'chose', 'point',
        'moment', 'temps', 'place', 'partie', 'aspect', 'niveau', 'terme',
        'situation', 'fait', 'raison', 'question', 'sujet', 'domaine', 'secteur',
        'contexte', 'exemple', 'problème', 'solution', 'approche', 'méthode',
        'processus', 'système', 'cadre', 'concept', 'notion', 'idée', 'pensée',
        'réflexion', 'vision', 'perspective', 'angle', 'jour', 'jours', 'année',
        'années', 'mois', 'fois', 'période', 'époque', 'heure', 'heures'
    }
    
    # Adjectifs qualificatifs acceptés (IA/technologies)
    accepted_adjectives = {
        'intelligent', 'artificiel', 'automatisé', 'numérique', 'technologique',
        'innovant', 'performant', 'avancé', 'moderne', 'efficace', 'rapide',
        'professionnel', 'automatique', 'interactif', 'intégré', 'collaboratif',
        'scalable', 'robuste', 'flexible', 'adaptable', 'sécurisé', 'fiable',
        'puissant', 'optimisé', 'distribué', 'cloud', 'virtuel', 'réel',
        'augmenté', 'décentralisé', 'transparent', 'traçable', 'impactant',
        'précis', 'utile', 'simple', 'complexe', 'stable', 'dynamique',
        'stratégique', 'tactique', 'opérationnel', 'fonctionnel', 'pratique',
        'environnemental', 'sociétal', 'humain'
    }
    
    # Verbes à l'infinitif acceptés
    accepted_verbs = {
        'analyser', 'automatiser', 'optimiser', 'améliorer', 'transformer',
        'générer', 'prédire', 'traiter', 'extraire', 'classifier', 'déterminer',
        'adapter', 'intégrer', 'développer', 'implémenter', 'déployer', 'gérer',
        'surveiller', 'monitorer', 'documenter', 'archiver', 'partager', 'collaborer',
        'apprendre', 'reconnaître', 'identifier', 'valider', 'vérifier', 'tester',
        'mémoriser', 'encoder', 'décoder', 'compresser', 'décompresser', 'crypter',
        'évaluer', 'mesurer', 'estimer', 'calculer', 'résoudre', 'simplifier',
        'concevoir', 'créer', 'produire', 'utiliser', 'exploiter'
    }
    
    keywords_found = []
    
    # Extraire les acronymes (mots en majuscules de 2+ caractères)
    acronyms = re.findall(r'\b[A-Z]{2,}\b', text)
    keywords_found.extend(acronyms)
    
    # Extraire les noms propres (mots commençant par majuscule)
    proper_nouns = re.findall(r'\b[A-Z][a-zàâäæçéèêëïîôóœùûüœñ]+\b', text)
    keywords_found.extend(proper_nouns)
    
    # Extraire et filtrer les autres mots
    text_lower = text.lower()
    words = re.findall(r'\b[a-zàâäæçéèêëïîôóœùûüñ]{3,}\b', text_lower)
    
    # Classifier les mots
    for word in words:
        # Vérifier les exclusions d'abord
        if word in stopwords_fr:
            continue
        if word in pronouns:
            continue
        if word in conjunctions:
            continue
        if word in adverbs_quantifiers:
            continue
        if word in vague_words:
            continue
        
        # Exclure les adverbes (-ment, -amment, etc.)
        if any(word.endswith(ending) for ending in adverbs_endings):
            if word not in accepted_adjectives and word not in accepted_verbs:
                continue
        
        # Vérifier si c'est un verbe à l'infinitif
        if word in accepted_verbs:
            keywords_found.append(word)
        # Vérifier si c'est un adjectif accepté
        elif word in accepted_adjectives:
            keywords_found.append(word)
        # Sinon, considérer comme nom commun
        elif len(word) > 4 and word not in stopwords_fr and word not in vague_words:
            # Vérifier que ce n'est pas un adverbe masqué
            if not any(word.endswith(ending) for ending in adverbs_endings):
                keywords_found.append(word)
    
    # Compter les occurrences et scorer
    word_freq = Counter(keywords_found)
    top_words = word_freq.most_common(30)
    
    # Score combiné: fréquence + longueur
    scored_words = [
        (word, freq * (1 + len(word) / 20)) 
        for word, freq in top_words
    ]
    scored_words.sort(key=lambda x: x[1], reverse=True)
    
    # Retourner les 8 meilleurs mots-clés uniques
    final_keywords = []
    seen = set()
    for word, score in scored_words:
        if word.lower() not in seen:
            final_keywords.append(word)
            seen.add(word.lower())
            if len(final_keywords) >= 8:
                break
    
    return final_keywords if final_keywords else ['analyse', 'interview']

def analyze_sentiment(text):
    """Analyse simple du sentiment"""
    positive_words = {'bon', 'bien', 'excellent', 'super', 'génial', 'merveilleux', 'positif'}
    negative_words = {'mauvais', 'mal', 'horrible', 'terrible', 'catastrophe', 'négatif'}
    
    text_lower = text.lower()
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)
    
    if pos_count > neg_count:
        return "Sentiment général positif ✓"
    elif neg_count > pos_count:
        return "Sentiment général négatif ✗"
    else:
        return "Sentiment équilibré"

@app.route('/')
def index():
    return send_from_directory('.', 'accueil.html')

@app.route('/analyse')
def analyse():
    return send_from_directory('.', 'analyse.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        # Vérifier si c'est un fichier audio ou du texte
        if 'audio' in request.files:
            # Traiter un fichier audio
            file = request.files['audio']
            
            if file.filename == '':
                return jsonify({"error": "Aucun fichier sélectionné"}), 400
            
            # Sauvegarder le fichier temporairement
            upload_folder = 'audios'
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, file.filename)
            file.save(filepath)
            
            # Nettoyage audio amélioré
            from audio_nettoyage import prepare_audio
            print("🔊 Nettoyage audio en cours...")
            cleaned_filepath = prepare_audio(filepath, volume_db=15)
            
            # Transcrire l'audio nettoyé
            print(f"📝 Transcription de {filepath}...")
            result = whisper_model.transcribe(cleaned_filepath, language="fr")
            transcription = result.get("text", "")
            
        elif 'text' in request.form:
            # Traiter du texte direct
            transcription = request.form.get('text', '')
            if not transcription:
                return jsonify({"error": "Aucun texte fourni"}), 400
        else:
            return jsonify({"error": "Aucun fichier audio ou texte fourni"}), 400
        
        if not transcription:
            return jsonify({"error": "Impossible de transcrire l'audio"}), 400
        
        # Générer le résumé
        print("Génération du résumé...")
        summary_text = summarize_with_t5(transcription)
        
        # Convertir le résumé en 2 paragraphes
        sentences = summary_text.split('. ')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Diviser les phrases en 2 groupes
        mid = len(sentences) // 2
        paragraph1 = '. '.join(sentences[:mid]) + '.' if sentences[:mid] else sentences[0] + '.'
        paragraph2 = '. '.join(sentences[mid:]) + '.' if sentences[mid:] else ''
        
        summary_paragraphs = [paragraph1]
        if paragraph2:
            summary_paragraphs.append(paragraph2)
        
        # Extraire mots-clés du RÉSUMÉ (plus propre) et sentiments de la TRANSCRIPTION
        keywords = extract_keywords(summary_text)
        sentiment = analyze_sentiment(transcription)
        
        return jsonify({
            "transcription": transcription,
            "summary": summary_paragraphs,
            "keywords": keywords,
            "sentiments": sentiment
        }), 200
    
    except Exception as e:
        print(f"Erreur: {str(e)}")
        return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

if __name__ == '__main__':
    # Ouvrir le navigateur automatiquement après 1 seconde
    def open_browser():
        time.sleep(1)  # Attendre que le serveur démarre
        webbrowser.open('http://localhost:5050')
    
    # Lancer l'ouverture du navigateur dans un thread séparé
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    print("🚀 Serveur démarrage sur http://localhost:5050...")
    app.run(debug=True, host='localhost', port=5050)
