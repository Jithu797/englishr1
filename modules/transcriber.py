import speech_recognition as sr

def transcribe_audio_local(file_path: str) -> str:
    """
    Transcribe audio locally using SpeechRecognition (Google Web API).
    Free but works best for short clips (<1 min).
    """
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(file_path) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio)
        return text
    except Exception as e:
        return f"Error during transcription: {e}"
