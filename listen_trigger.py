import speech_recognition as sr
import subprocess
import os
import time
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav

# Settings
DURATION = 2.0  
SAMPLE_RATE = 16000
MIC_DEVICE_INDEX = 1  
TEMP_AUDIO = "temp_trigger.wav"
PROJECT_PATH = r"D:\Voice-Python-Assistant"  # ඔයාගේ ෆෝල්ඩර් පාත් එක මෙතැනට දෙන්න

def listen_for_trigger():
    r = sr.Recognizer()
    while True:
        try:
            # පසුබිමින් සයිලන්ට් විදිහට මයික්‍රෆෝනයෙන් අහගෙන ඉන්නවා
            audio_data = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype=np.int16, device=MIC_DEVICE_INDEX)
            sd.wait()
            
            wav.write(TEMP_AUDIO, SAMPLE_RATE, audio_data)
            
            with sr.AudioFile(TEMP_AUDIO) as source:
                audio = r.record(source)
                try:
                    text = r.recognize_google(audio, language='en-US').lower()
                    if "open luna" in text or "luna" in text or "ලුනා" in text:
                        print("[TRIGGER] Luna activation detected!")
                        # ඩිරෙක්ට්ම Fullscreen Luna Core එක ඕපන් කිරීම
                        os.chdir(PROJECT_PATH)
                        subprocess.Popen(["python", "luna_core.py"])
                        time.sleep(10)  # ලූනා ඕපන් වුණු පසු ටික වේලාවක් බලා සිටීම
                except:
                    pass
        except Exception as e:
            pass
        
        if os.path.exists(TEMP_AUDIO):
            try:
                os.remove(TEMP_AUDIO)
            except:
                pass
        time.sleep(0.5)

if __name__ == "__main__":
    print("[SYSTEM] Background Luna Trigger is active and listening...")
    listen_for_trigger()