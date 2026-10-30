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

# --- Gemini API Configuration ---
GOOGLE_API_KEY = "YOUR_GEMINI_API_KEY"  # හෝ os.getenv("GEMINI_API_KEY")  # මෙතැනට ඔයාගේ API Key එක දාන්න
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel('gemini-3.8-flash')

DURATION = 2.5  
SAMPLE_RATE = 16000
MIC_DEVICE_INDEX = 1  
TEMP_AUDIO = "temp_voice.wav"

class LunaRobotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LUNA - Sinhala & English AI Assistant")
        self.root.geometry("520x620")
        self.root.config(bg="#12121a")
        self.root.resizable(False, False)

        self.is_running = True
        self.is_speaking = False
        self.current_color = "#ff69b4" 

        # Title Header
        self.title_label = tk.Label(root, text="L U N A   A I   ( සිංහල & English )", font=("Courier", 13, "bold"), fg="#00ffff", bg="#12121a")
        self.title_label.pack(pady=15)

        # Robot Head Canvas
        self.canvas_size = 300
        self.canvas = tk.Canvas(root, width=self.canvas_size, height=self.canvas_size, bg="#08080c", highlightthickness=3, highlightbackground="#00ffff")
        self.canvas.pack(pady=10)

        cx, cy = self.canvas_size / 2, self.canvas_size / 2

        # Robot Head Rim
        self.head_rim = self.canvas.create_oval(cx - 130, cy - 130, cx + 130, cy + 130, outline="#333344", width=6)
        
        # Inner Screen Display
        self.screen = self.canvas.create_oval(cx - 115, cy - 115, cx + 115, cy + 115, fill="#000000", outline="#ff69b4", width=3)

        # Glowing Eyes
        self.eye_left = self.canvas.create_oval(cx - 55, cy - 45, cx - 20, cy + 10, outline="#ff69b4", width=4, fill="#08080c")
        self.eye_right = self.canvas.create_oval(cx + 20, cy - 45, cx + 55, cy + 10, outline="#ff69b4", width=4, fill="#08080c")

        # Mouth
        self.mouth = self.canvas.create_arc(cx - 45, cy + 20, cx + 45, cy + 70, start=190, extent=160, style=tk.ARC, outline="#ff69b4", width=4)

        # Status Display Label
        self.status_label = tk.Label(root, text="STATUS: SLEEPING", font=("Courier", 12, "bold"), fg="#ff69b4", bg="#12121a")
        self.status_label.pack(pady=10)

        # Log Box
        self.log_box = tk.Text(root, height=6, width=54, font=("Consolas", 9), bg="#1c1c28", fg="#00ffcc", relief=tk.FLAT)
        self.log_box.pack(pady=10)
        self.log_box.insert(tk.END, "[SYSTEM] gTTS Voice Core Initialized.\n[INFO] Ready for Sinhala & English speech...\n")
        self.log_box.config(state=tk.DISABLED)

        # Threads
        self.anim_thread = threading.Thread(target=self.robot_animation_loop)
        self.anim_thread.daemon = True
        self.anim_thread.start()

        self.assistant_thread = threading.Thread(target=self.run_assistant_loop)
        self.assistant_thread.daemon = True
        self.assistant_thread.start()

    def update_appearance(self, status_text, color):
        self.status_label.config(text=f"STATUS: {status_text}", fg=color)
        self.current_color = color
        self.canvas.itemconfig(self.screen, outline=color)
        self.canvas.itemconfig(self.eye_left, outline=color)
        self.canvas.itemconfig(self.eye_right, outline=color)
        self.canvas.itemconfig(self.mouth, outline=color)

    def log(self, message):
        self.log_box.config(state=tk.NORMAL)
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)
        self.log_box.config(state=tk.DISABLED)

    def robot_animation_loop(self):
        cx, cy = self.canvas_size / 2, self.canvas_size / 2
        talk_state = 0

        while self.is_running:
            try:
                if self.is_speaking:
                    if talk_state == 0:
                        self.canvas.coords(self.mouth, cx - 40, cy + 15, cx + 40, cy + 65)
                        self.canvas.itemconfig(self.mouth, extent=180, style=tk.CHORD, fill=self.current_color)
                        talk_state = 1
                    else:
                        self.canvas.coords(self.mouth, cx - 30, cy + 30, cx + 30, cy + 50)
                        self.canvas.itemconfig(self.mouth, extent=180, style=tk.ARC, fill="")
                        talk_state = 0
                    time.sleep(0.12)
                else:
                    self.canvas.coords(self.mouth, cx - 45, cy + 20, cx + 45, cy + 70)
                    self.canvas.itemconfig(self.mouth, extent=160, style=tk.ARC, fill="")
                    
                    if random.random() < 0.1:  
                        self.canvas.coords(self.eye_left, cx - 55, cy - 20, cx - 20, cy - 15)
                        self.canvas.coords(self.eye_right, cx + 20, cy - 20, cx + 55, cy - 15)
                        time.sleep(0.1)
                        self.canvas.coords(self.eye_left, cx - 55, cy - 45, cx - 20, cy + 10)
                        self.canvas.coords(self.eye_right, cx + 20, cy - 45, cx + 55, cy + 10)
                    
                    time.sleep(0.3)
            except:
                break

    def speak(self, text):
        self.log(f"🤖 Luna: {text}")
        self.is_speaking = True
        
        # Check if text contains Sinhala characters
        has_sinhala = any('\u0d80' <= char <= '\u0dff' for char in text)
        
        try:
            if has_sinhala:
                # Use Google TTS for Sinhala
                tts = gTTS(text=text, lang='si')
                speech_file = "temp_speech.mp3"
                tts.save(speech_file)
                
                # Play using default system startfile (no welcome screens!)
                os.startfile(speech_file)
                time.sleep(4)
                
                if os.path.exists(speech_file):
                    try:
                        os.remove(speech_file)
                    except:
                        pass
            else:
                # Use pyttsx3 for English (faster)
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
        self.speak("Hello Vinosha! I am ready. Say Hey Luna to wake me up.")
        
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
                            self.speak("Opening Notepad. I am ready to type what you say. Say stop typing when you are done.")
                            subprocess.Popen(["notepad.exe"])
                            time.sleep(1.5)
                            
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
    app = LunaRobotApp(root)
    root.mainloop()