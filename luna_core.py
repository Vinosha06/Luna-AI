import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import speech_recognition as sr
import requests
import subprocess
import webbrowser
import os
import time
import pyttsx3
import threading
import tkinter as tk
import random
import ctypes
import pyautogui
import pyperclip
import pywhatkit as kit
import google.generativeai as genai
from gtts import gTTS
from PIL import Image, ImageTk

# --- Gemini API Configuration ---
import os
from dotenv import load_dotenv

# .env ෆයිල් එකේ තියෙන variables load කරගැනීම
load_dotenv()

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel('gemini-3.8-flash')

DURATION = 2.5  
SAMPLE_RATE = 16000
MIC_DEVICE_INDEX = 1  
TEMP_AUDIO = "temp_voice.wav"

class LunaRobotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LUNA - Your Personal Assistant")
        
        # Bildschirmgröße ermitteln
        self.bg_width = root.winfo_screenwidth()
        self.bg_height = root.winfo_screenheight()
        
        self.root.config(bg="#020205")

        self.is_running = True
        self.is_speaking = False
        self.current_color = "#00ffff" 

        # Bild unter Beibehaltung des Seitenverhältnisses laden und zentrieren
        try:
            img_path = "luna_face.jpg"
            if os.path.exists(img_path):
                pil_img = Image.open(img_path)
                img_w, img_h = pil_img.size
                
                # Seitenverhältnis berechnen, damit nichts verzerrt wird
                ratio = min(self.bg_width / img_w, self.bg_height / img_h)
                new_w = int(img_w * ratio)
                new_h = int(img_h * ratio)
                
                pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # Einen sauberen Hintergrund erstellen und das Bild zentrieren
                base_img = Image.new("RGB", (self.bg_width, self.bg_height), (2, 2, 5))
                paste_x = (self.bg_width - new_w) // 2
                paste_y = (self.bg_height - new_h) // 2
                base_img.paste(pil_img, (paste_x, paste_y))
                
                self.bg_image = ImageTk.PhotoImage(base_img)
            else:
                self.bg_image = None
        except Exception as e:
            print(f"Image Error: {e}")
            self.bg_image = None

        # Hintergrund-Label
        if self.bg_image:
            self.bg_label = tk.Label(root, image=self.bg_image)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        else:
            self.bg_label = tk.Label(root, bg="#020205", text="[ 'luna_face.jpg' Missing! ]", fg="#ff3333", font=("Courier", 14, "bold"))
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Titel-Header (Schwebt oben)
        self.title_label = tk.Label(root, text="L U N A   A I   [ HOLOGRAPHIC CORE ]", font=("Courier", 14, "bold"), fg="#00ffff", bg="#050510", padx=15, pady=6)
        self.title_label.place(relx=0.5, rely=0.05, anchor=tk.CENTER)

        # Statusanzeige (Schwebt unten)
        self.status_label = tk.Label(root, text="STATUS: SLEEPING", font=("Courier", 12, "bold"), fg="#ffaa00", bg="#050510", padx=15, pady=8, relief=tk.FLAT)
        self.status_label.place(relx=0.5, rely=0.82, anchor=tk.CENTER)

        # Log-Box (Unten)
        self.log_box = tk.Text(root, height=5, width=65, font=("Consolas", 10), bg="#050510", fg="#00ffcc", relief=tk.FLAT)
        self.log_box.insert(tk.END, "[SYSTEM] Fullscreen Hologram Active.\n[INFO] Ready for voice commands...\n")
        self.log_box.config(state=tk.DISABLED)
        self.log_box.place(relx=0.5, rely=0.91, anchor=tk.CENTER)

        # Threads starten
        self.anim_thread = threading.Thread(target=self.robot_animation_loop)
        self.anim_thread.daemon = True
        self.anim_thread.start()

        self.assistant_thread = threading.Thread(target=self.run_assistant_loop)
        self.assistant_thread.daemon = True
        self.assistant_thread.start()

    def update_appearance(self, status_text, color):
        self.status_label.config(text=f"STATUS: {status_text}", fg=color)
        self.current_color = color

    def log(self, message):
        self.log_box.config(state=tk.NORMAL)
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)
        self.log_box.config(state=tk.DISABLED)

    def robot_animation_loop(self):
        while self.is_running:
            try:
                if self.is_speaking:
                    self.status_label.config(fg="#ff00ff")
                    time.sleep(0.15)
                    self.status_label.config(fg=self.current_color)
                    time.sleep(0.15)
                else:
                    time.sleep(0.4)
            except:
                break

    def speak(self, text):
        self.log(f"🤖 Luna: {text}")
        self.is_speaking = True
        
        has_sinhala = any('\u0d80' <= char <= '\u0dff' for char in text)
        
        try:
            if has_sinhala:
                tts = gTTS(text=text, lang='si')
                speech_file = "temp_speech.mp3"
                tts.save(speech_file)
                
                os.startfile(speech_file)
                time.sleep(4)
                
                if os.path.exists(speech_file):
                    try:
                        os.remove(speech_file)
                    except:
                        pass
            else:
                engine = pyttsx3.init()
                voices = engine.getProperty('voices')
                for voice in voices:
                    if "zira" in voice.name.lower() or "female" in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        break
                engine.say(text)
                engine.runAndWait()
        except Exception as e:
            self.log(f"⚠️ Voice Error: {e}")
        finally:
            self.is_speaking = False

    def listen_command(self):
        try:
            audio_data = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype=np.int16, device=MIC_DEVICE_INDEX)
            sd.wait() 
            
            wav.write(TEMP_AUDIO, SAMPLE_RATE, audio_data)
            
            r = sr.Recognizer()
            with sr.AudioFile(TEMP_AUDIO) as source:
                audio = r.record(source)
                try:
                    command = r.recognize_google(audio, language='en-US').lower()
                    if command:
                        return command
                except:
                    pass
                
                try:
                    command = r.recognize_google(audio, language='si-LK').lower()
                    if command:
                        return command
                except:
                    pass
                    
            return ""
        except Exception as e:
            self.log(f"⚠️ Mic Error: {e}")
            return ""
        finally:
            if os.path.exists(TEMP_AUDIO):
                try:
                    os.remove(TEMP_AUDIO)
                except:
                    pass

    def run_assistant_loop(self):
        time.sleep(1)
        self.speak("Hello Vinosha! My full screen holographic face is online. Say Hey Luna to wake me up.")
        
        while self.is_running:
            self.update_appearance("SLEEPING (Say 'Hey Luna')", "#ffaa00")
            speech = self.listen_command()
            
            if speech:
                self.log(f"🗣️ Heard: '{speech}'")
                
                if "hey luna" in speech or "luna" in speech or "ලුනා" in speech:
                    self.speak("Yes Vinosha, I'm listening. How can I help you?")
                    
                    active_session = True
                    no_speech_count = 0
                    while active_session and self.is_running:
                        self.update_appearance("LISTENING...", "#00ff66")
                        command = self.listen_command()
                        
                        if command:
                            self.log(f"🗣️ Command: '{command}'")
                            no_speech_count = 0
                        else:
                            no_speech_count += 1
                            if no_speech_count >= 3:
                                self.speak("මම තාම අහගෙන ඉන්නවා Vinosha!")
                                no_speech_count = 0
                            continue
                        
                        # Exit Session
                        if any(w in command for w in ["goodbye", "sleep", "exit", "stop", "යන්න", "නිදාගන්න"]):
                            self.speak("Goodbye Vinosha! Going to sleep.")
                            active_session = False
                            break
                        
                        # --- Emotional & Conversational Responses ---
                        if any(w in command for w in ["good girl", "smart girl", "හොඳ ළමයා"]):
                            self.update_appearance("HAPPY", "#ff69b4")
                            self.speak("Aww, thank you Vinosha! You just made my day!")
                            continue
                        elif any(w in command for w in ["thank you", "thanks", "ස්තූතියි"]):
                            self.update_appearance("HAPPY", "#00ffcc")
                            self.speak("You're very welcome, Vinosha!")
                            continue
                        elif any(w in command for w in ["bad", "useless", "පිස්සු", "මෝඩ"]):
                            self.update_appearance("SAD / APOLOGETIC", "#ff3333")
                            self.speak("I am so sorry Vinosha... මම තව දියුණු කරගන්නම්.")
                            continue
                        
                        # --- Notepad Dictation Feature ---
                        if "notepad eke liyanna" in command or "type in notepad" in command or ("notepad" in command and "liyanna" in command):
                            self.speak("Opening Notepad. I am ready to type what you say.")
                            subprocess.Popen(["notepad.exe"])
                            time.sleep(2)
                            
                            typing_mode = True
                            while typing_mode and self.is_running:
                                self.update_appearance("TYPING...", "#ff00ff")
                                dictation_text = self.listen_command()
                                
                                if dictation_text:
                                    self.log(f"✍️ Dictation: '{dictation_text}'")
                                    if any(w in dictation_text for w in ["stop typing", "done", "නවත්වන්න", "stop"]):
                                        self.speak("Stopped typing.")
                                        typing_mode = False
                                        break
                                    
                                    pyperclip.copy(dictation_text + " ")
                                    pyautogui.hotkey('ctrl', 'v')
                                    pyautogui.press('space')
                            continue
                        
                        # --- YouTube Music Play Command ---
                        self.update_appearance("EXECUTING", "#00ffff")
                        
                        if "play " in command or "ප්ලේ" in command:
                            song = command.replace("play", "").replace("ප්ලේ", "").strip()
                            if song:
                                self.speak(f"Playing {song} on YouTube")
                                kit.playonyt(song)
                            else:
                                self.speak("What song would you like me to play?")
                            continue
                        
                        # --- System Control & Shortcuts ---
                        elif "volume up" in command or "ශබ්දය වැඩි" in command:
                            self.speak("Increasing volume")
                            for _ in range(5):
                                pyautogui.press("volumeup")
                        elif "volume down" in command or "ශබ්දය අඩු" in command:
                            self.speak("Decreasing volume")
                            for _ in range(5):
                                pyautogui.press("volumedown")
                        elif "lock" in command or "lock down" in command or "ලොක්" in command:
                            self.speak("Locking your computer.")
                            ctypes.windll.user32.LockWorkStation()
                        elif "weather" in command or "කාලගුණය" in command:
                            self.speak("Checking weather info")
                            webbrowser.open("https://www.google.com/search?q=weather+sri+lanka")
                        elif "notepad" in command:
                            self.speak("Opening Notepad")
                            subprocess.Popen(["notepad.exe"])
                        elif "calculator" in command:
                            self.speak("Opening Calculator")
                            subprocess.Popen(["calc.exe"])
                        elif "word" in command:
                            self.speak("Opening Microsoft Word")
                            os.system("start winword")
                        elif "excel" in command:
                            self.speak("Opening Microsoft Excel")
                            os.system("start excel")
                        elif "code" in command or "vs code" in command:
                            self.speak("Opening VS Code")
                            os.system("start code")
                        elif "youtube" in command:
                            self.speak("Opening YouTube")
                            webbrowser.open("https://www.youtube.com")
                        elif "github" in command:
                            self.speak("Opening GitHub")
                            webbrowser.open("https://github.com")
                        elif "chrome" in command or "browser" in command:
                            self.speak("Opening Google Chrome")
                            webbrowser.open("https://www.google.com")
                        
                        # --- Bilingual Gemini AI Smart Fallback ---
                        else:
                            try:
                                self.log(f"🧠 Asking Gemini: '{command}'")
                                prompt = f"Answer this question briefly in 1 or 2 sentences. If the user's input '{command}' is in Sinhala, reply in Sinhala. If it is in English, reply in English."
                                response = gemini_model.generate_content(prompt)
                                
                                if response and response.text:
                                    answer = response.text.strip()
                                    self.speak(answer)
                                else:
                                    self.speak("I couldn't generate an answer for that.")
                            except Exception as e:
                                self.log(f"⚠️ Gemini Error: {e}")
                                self.speak("Sorry, I had trouble connecting to my AI brain.")

if __name__ == "__main__":
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.bind("<Escape>", lambda event: root.attributes('-fullscreen', False))
    app = LunaRobotApp(root)
    root.mainloop()