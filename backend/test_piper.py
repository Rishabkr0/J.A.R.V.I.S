import os
import sys
import wave
import numpy as np
import logging
import piper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_piper")

def test_piper():
    model_path = os.path.join("data", "en_US-lessac-low.onnx")
    model_json = os.path.join("data", "en_US-lessac-low.onnx.json")
    
    if not os.path.exists(model_path):
        logger.error(f"PIPER MODEL MISSING: '{model_path}' not found!")
        return False
        
    output_wav = os.path.join("data", "test_output.wav")
    text = "Hello. I am JARVIS."
    
    try:
        voice = piper.PiperVoice.load(model_path, config_path=model_json)
        
        with wave.open(output_wav, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(voice.config.sample_rate)
            
            total_samples = 0
            for chunk in voice.synthesize(text):
                audio_int16 = (chunk.audio_float_array * 32767).astype(np.int16)
                wav_file.writeframes(audio_int16.tobytes())
                total_samples += len(audio_int16)
                
        file_size = os.path.getsize(output_wav)
        duration = total_samples / voice.config.sample_rate
        logger.info(f"SUCCESS! Audio file generated: {output_wav} ({file_size} bytes, duration: {duration:.2f}s, sample rate: {voice.config.sample_rate}Hz)")
        return True
    except Exception as e:
        logger.error(f"Piper execution failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_piper()
    sys.exit(0 if success else 1)
