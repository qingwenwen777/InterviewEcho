import sys
import os
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_path)

from services.stt_service import stt_service
import torch

def test_whisper():
    print("Testing Whisper...")
    print(f"CUDA available: {torch.cuda.is_available()}")
    try:
        # Create a dummy silent audio or just check model loading
        print("Loading model...")
        model = stt_service.load_model("small")
        print("Model loaded successfully.")
        
        # Check ffmpeg
        import subprocess
        try:
            subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
            print("FFmpeg is accessible from Python.")
        except Exception as fe:
            print(f"FFmpeg check failed: {fe}")
            print("Whisper will NOT be able to transcribe audio files without FFmpeg.")

        print("Whisper setup seems correct.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_whisper()
