import os
import subprocess
import logging

logger = logging.getLogger(__name__)

def prepare_audio(input_file, output_dir="processed", volume_db=10):
    """
    Prépare un fichier audio pour la transcription Whisper :
    - Normalise le volume (peak normalization)
    - Réduit le bruit avec plusieurs techniques
    - Applique compression dynamique
    - Améliore la clarté des voix
    - Convertit en mono, 16kHz
    - Retourne le chemin du fichier traité

    Args:
        input_file (str): chemin du fichier audio original
        output_dir (str): dossier où sauvegarder le fichier traité
        volume_db (float): gain supplémentaire en dB

    Returns:
        str: chemin du fichier audio préparé
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Fichier audio introuvable: {input_file}")

    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(output_dir, f"{base_name}_processed.wav")

    # Chaîne d'amélioration audio complexe:
    # 1. highpass: supprime les bruits graves (< 50Hz)
    # 2. lowpass: supprime les très hautes fréquences
    # 3. afftdn: réduction de bruit FFT
    # 4. compand: compression dynamique (rend l'audio plus uniforme)
    # 5. volume: normalise et augmente le volume
    # 6. speechnorm: normalise la parole spécifiquement
    
    audio_filter = (
        "highpass=f=50,"              # Supprime fréquences < 50Hz (bruit de fond)
        "lowpass=f=8000,"             # Supprime fréquences > 8000Hz (hum)
        "afftdn=om=o,"                # Réduction bruit spectral
        "anlmdn=f=0.01:o=o:p=0.0025," # Réduction bruit adaptative (voix-friendly)
        "compand=attacks=0.005:decays=0.07:points=-80/-80|-50/-40|-30/-30|0/0:soft-knee=6:gain=6," # Compression dynamique
        "speechnorm=e=12500:t=0.5,"   # Normalisation spécifique à la parole
        f"volume={volume_db}dB"       # Augmente le volume final
    )

    # Commande ffmpeg
    cmd = [
        "ffmpeg",
        "-y",           # overwrite
        "-i", input_file,
        "-af", audio_filter,
        "-ar", "16000", # sample rate 16kHz (optimal Whisper)
        "-ac", "1",     # mono (plus efficace pour la parole)
        "-q:a", "0",    # meilleure qualité
        output_file
    ]

    try:
        print(f"🔊 Nettoyage audio avancé de {input_file}...")
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info(f"Audio préparé: {output_file}")
        print(f"✅ Audio préparé: {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        logger.exception("Erreur lors du traitement audio: %s", error_msg)
        print(f"❌ Erreur: {error_msg}")
        # Si ffmpeg échoue, retourner le fichier original
        return input_file

