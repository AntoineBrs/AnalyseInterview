import os
import whisper
from transformers import T5Tokenizer, T5ForConditionalGeneration
from audio_nettoyage import prepare_audio 

# --- Config Whisper ---
whisper_model = whisper.load_model("base")

# --- Config T5 ---
t5_model_name = "plguillou/t5-base-fr-sum-cnndm"
tokenizer = T5Tokenizer.from_pretrained(t5_model_name)
t5_model = T5ForConditionalGeneration.from_pretrained(t5_model_name)

# --- Fonction de résumé T5 ---
def summarize_with_t5(text, max_input_tokens=1024, max_output_tokens=450, min_output_tokens=250):
    """Résumé avec T5 en français"""
    input_text = "summarize: " + text
    inputs = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=max_input_tokens)

    summary_ids = t5_model.generate(
        inputs["input_ids"],
        max_length=max_output_tokens,
        min_length=min_output_tokens,
        length_penalty=2.0,
        num_beams=8,
        no_repeat_ngram_size=3,
        early_stopping=True,
        do_sample=False
    )
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

# --- Fichier audio à traiter ---
audio_file = "interview.mp3"
if not os.path.exists(audio_file):
    raise FileNotFoundError(f"{audio_file} introuvable dans le dossier courant")

# --- Nettoyage et préparation de l'audio ---
processed_path = prepare_audio(audio_file, volume_db=10)

# --- Transcription Whisper ---
result = whisper_model.transcribe(processed_path, language="fr")
transcription = result.get("text", "")

print("=== Transcription ===\n")
print(transcription)

# --- Résumé T5 ---
summary = summarize_with_t5(transcription, max_input_tokens=1024, max_output_tokens=450, min_output_tokens=250)
print("\n=== Résumé ===\n")
print(summary)