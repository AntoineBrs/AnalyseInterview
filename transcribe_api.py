from flask import Flask, request, jsonify
import whisper
import os
import logging
from flask_cors import CORS  # <-- Ajoute cette ligne

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
