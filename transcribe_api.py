from flask import Flask, request, jsonify
import whisper
import os
import logging
import requests
from flask_cors import CORS  # <-- Ajoute cette ligne
try:
    from huggingface_hub import InferenceApi
except Exception:
    InferenceApi = None

app = Flask(__name__)
# Autoriser explicitement toutes les origines (utile si la page est servie en file:// ou depuis un autre port)
CORS(app, resources={r"/*": {"origins": "*"}}) # <-- Ajoute cette ligne (avant toute route)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger le modèle une seule fois au démarrage
try:
    model = whisper.load_model("base")
    logger.info("Whisper model loaded successfully")
except Exception as e:
    logger.exception("Failed to load Whisper model: %s", e)
    model = None

ALLOWED_EXT = {'.mp3', '.wav', '.m4a', '.flac', '.ogg'}


def allowed_file(filename):
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXT


def summarize_with_hf(text, hf_token, model="mrm8488/mbart-large-finetuned-xlsum", max_length=150, min_length=30):
    """Use Hugging Face Inference API to summarize text.
    Requires HF token in environment variable `HF_API_TOKEN` or passed in.
    The `model` can be changed to a French-capable summarization model if needed.
    """
    # Prefer huggingface_hub.InferenceApi if available (more ergonomic)
    if InferenceApi is not None:
        try:
            client = InferenceApi(repo_id=model, token=hf_token)
            # The InferenceApi call returns either a string, list, or structured response
            resp = client(inputs=text, parameters={"max_length": max_length, "min_length": min_length})
            # If it's list of dicts with 'summary_text'
            if isinstance(resp, list) and len(resp) > 0 and isinstance(resp[0], dict) and 'summary_text' in resp[0]:
                return resp[0]['summary_text']
            # If it's a simple list of strings
            if isinstance(resp, list) and all(isinstance(r, str) for r in resp):
                return "\n".join(resp)
            # If it's a dict with summary_text
            if isinstance(resp, dict) and 'summary_text' in resp:
                return resp['summary_text']
            # If it's just a string
            if isinstance(resp, str):
                return resp
        except Exception:
            logger.exception("huggingface_hub InferenceApi call failed, will fallback to HTTP request")

    # Fallback: use direct HTTP Inference API (requests)
    api_url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {hf_token}"}
    payload = {
        "inputs": text,
        "parameters": {"max_length": max_length, "min_length": min_length},
    }
    try:
        resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        # HF returns a list of dicts with 'summary_text' usually
        if isinstance(data, list) and len(data) > 0 and 'summary_text' in data[0]:
            return data[0]['summary_text']
        # sometimes the model returns a simple string or other structure
        if isinstance(data, dict) and 'summary_text' in data:
            return data['summary_text']
        # fallback: try join if list of strings
        if isinstance(data, list) and all(isinstance(d, str) for d in data):
            return "\n".join(data)
        return None
    except Exception as e:
        logger.exception("Hugging Face summarization failed (HTTP fallback): %s", e)
        return None


def summarize_with_transformers(text, model_name="mrm8488/mbart-large-finetuned-xlsum", max_length=150, min_length=30):
    """Try local summarization with transformers pipeline if installed.
    This requires `transformers` and appropriate model weights downloaded.
    """
    try:
        from transformers import pipeline
        summarizer = pipeline("summarization", model=model_name)
        out = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
        if isinstance(out, list) and len(out) > 0 and 'summary_text' in out[0]:
            return out[0]['summary_text']
        return None
    except Exception:
        logger.exception("Local transformers summarization unavailable or failed")
        return None


@app.route('/transcribe', methods=['POST'])
def transcribe():
    if model is None:
        return jsonify({'error': 'Transcription model not loaded on server.'}), 500

    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file uploaded.'}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'Filename is empty.'}), 400

    if not allowed_file(audio_file.filename):
        return jsonify({'error': 'Unsupported file type. Allowed: ' + ", ".join(sorted(ALLOWED_EXT))}), 400

    uploads_dir = os.path.join(os.getcwd(), 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    file_path = os.path.join(uploads_dir, audio_file.filename)

    try:
        audio_file.save(file_path)
        logger.info("Saved uploaded file to %s", file_path)

        # Transcription: if ffmpeg is missing, whisper will raise an error here.
        result = model.transcribe(file_path, language='fr')
        transcription = result.get('text', '')
        logger.info("Transcription succeeded (len=%d)", len(transcription))
        return jsonify({'transcription': transcription})

    except Exception as e:
        logger.exception("Error during transcription: %s", e)
        # Return a safe error message to the client but keep server logs for details
        return jsonify({'error': 'Erreur serveur lors de la transcription. Vérifiez les logs du serveur. Détail: %s' % str(e)}), 500

    finally:
        # Nettoyage du fichier uploadé
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info("Removed uploaded file %s", file_path)
        except Exception:
            logger.exception("Failed to remove uploaded file %s", file_path)


if __name__ == '__main__':
    app.run(port=5000, debug=True)


@app.route('/summarize', methods=['POST'])
def summarize():
    """Endpoint to summarize text or audio.
    Usage:
    - Send JSON {"text": "..."} to summarize existing text.
    - Send form-data with key 'audio' to upload audio file (it will be transcribed then summarized).
    Optional form/json keys: max_length, min_length, model (huggingface model id).
    Requires either a Hugging Face API token in HF_API_TOKEN env var or locally installed `transformers`.
    """
    # Parameters
    max_length = int(request.form.get('max_length') or request.json.get('max_length') if request.is_json else request.form.get('max_length') or 150)
    min_length = int(request.form.get('min_length') or request.json.get('min_length') if request.is_json else request.form.get('min_length') or 30)
    model_name = (request.form.get('model') or (request.json.get('model') if request.is_json else None) or os.environ.get('HF_MODEL') or 'facebook/bart-large-cnn')

    text = None
    # If JSON with text
    if request.is_json:
        payload = request.get_json()
        text = payload.get('text')

    # If text field in form
    if not text and 'text' in request.form:
        text = request.form['text']

    # If audio uploaded, transcribe it first
    if 'audio' in request.files:
        audio_file = request.files['audio']
        if audio_file.filename == '' or not allowed_file(audio_file.filename):
            return jsonify({'error': 'No audio or unsupported audio file.'}), 400
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        file_path = os.path.join(uploads_dir, audio_file.filename)
        try:
            audio_file.save(file_path)
            logger.info("Saved uploaded file for summarization to %s", file_path)
            if model is None:
                return jsonify({'error': 'Transcription model not loaded on server.'}), 500
            result = model.transcribe(file_path, language='fr')
            text = result.get('text', '')
        except Exception as e:
            logger.exception("Error during transcription for summarization: %s", e)
            return jsonify({'error': 'Erreur lors de la transcription pour le résumé.'}), 500
        finally:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                logger.exception("Failed to remove uploaded file %s", file_path)

    if not text:
        return jsonify({'error': "Aucun texte fourni pour résumer."}), 400

    # Try Hugging Face Inference API first if token present
    hf_token = os.environ.get('HF_API_TOKEN')
    summary = None
    if hf_token:
        summary = summarize_with_hf(text, hf_token, model=model_name, max_length=max_length, min_length=min_length)

    
    if summary is None:
        summary = summarize_with_transformers(text, model_name=model_name, max_length=max_length, min_length=min_length)

    if summary is None:
        return jsonify({'error': 'Aucun résumeur disponible (configurer HF_API_TOKEN ou installer transformers).'}), 500

    return jsonify({'summary': summary})
