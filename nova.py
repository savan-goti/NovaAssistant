import speech_recognition as sr
import pyttsx3
import os
import webbrowser
import pyautogui
import datetime
import psutil
import logging
import json

# ---------------- CONFIG ----------------

COMMANDS_FILE = "learned_commands.json"

logging.basicConfig(
    filename="nova_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

engine = pyttsx3.init()
recognizer = sr.Recognizer()

# ---------------- UTILITIES ----------------

def log_interaction(entity, message):
    logging.info(f"{entity}: {message}")
    print(f"{entity}: {message}")

def speak(text):
    log_interaction("Nova", text)
    engine.say(text)
    engine.runAndWait()

def listen():
    with sr.Microphone() as source:
        print("\nListening...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio).lower()
            log_interaction("User", text)
            return text
        except:
            return ""

# ---------------- LEARNING MODE ----------------

def load_learned_commands():
    if not os.path.exists(COMMANDS_FILE):
        return {}
    with open(COMMANDS_FILE, "r") as f:
        return json.load(f)

def save_learned_commands(commands):
    with open(COMMANDS_FILE, "w") as f:
        json.dump(commands, f, indent=4)

learned_commands = load_learned_commands()

def learning_mode():
    speak("Learning mode activated. What should I listen for?")
    trigger = listen()

    if not trigger:
        speak("I didn't hear a trigger phrase.")
        return

    speak("What action should I perform?")
    action = listen()

    if not action:
        speak("I didn't hear the action.")
        return

    learned_commands[trigger] = action
    save_learned_commands(learned_commands)

    speak(f"I have learned the command {trigger}")

# ---------------- COMMAND PROCESSOR ----------------

def process_command(cmd):
    # --- Learning Mode ---
    if "learn new command" in cmd or "learning mode" in cmd:
        learning_mode()
        return

    # --- Learned Commands ---
    for trigger, action in learned_commands.items():
        if trigger in cmd:
            speak(f"Executing learned command {trigger}")
            if action.startswith("http"):
                webbrowser.open(action)
            else:
                os.startfile(action)
            return

    # --- Built-in Commands ---
    if "open chrome" in cmd:
        speak("Opening Chrome")
        os.startfile("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")

    elif "open spotify" in cmd:
        speak("Opening Spotify")
        try:
            os.system("start spotify")
        except:
            webbrowser.open("https://open.spotify.com")

    elif "open gmail" in cmd or "write email" in cmd:
        speak("Opening Gmail")
        webbrowser.open("https://mail.google.com")

    elif "time" in cmd:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {current_time}")

    elif "battery" in cmd:
        battery = psutil.sensors_battery()
        if battery:
            status = "plugged in" if battery.power_plugged else "not plugged in"
            speak(f"Battery is at {battery.percent} percent and {status}")
        else:
            speak("Battery info unavailable")

    elif "search" in cmd:
        query = cmd.replace("search", "").strip()
        if not query:
            speak("What should I search?")
            query = listen()
        if query:
            webbrowser.open(f"https://www.google.com/search?q={query}")
            speak(f"Searching {query}")

    elif "play" in cmd:
        query = cmd.replace("play", "").strip()
        if query:
            webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
            speak(f"Playing {query}")

    elif "screenshot" in cmd:
        speak("Taking screenshot")
        img = pyautogui.screenshot()
        filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        img.save(filename)
        speak("Screenshot saved")

    elif "volume up" in cmd:
        pyautogui.press("volumeup")

    elif "volume down" in cmd:
        pyautogui.press("volumedown")

    elif "mute" in cmd:
        pyautogui.press("volumemute")

    elif "close window" in cmd:
        pyautogui.hotkey("alt", "f4")

    elif "shutdown" in cmd:
        speak("Are you sure?")
        if "yes" in listen():
            speak("Shutting down")
            os.system("shutdown /s /t 5")

    elif "stop nova" in cmd or "exit" in cmd:
        speak("Goodbye")
        exit()

    else:
        speak("I don't know that yet. You can teach me.")

# ---------------- MAIN LOOP ----------------

print("Nova Assistant Starting...")
speak("Nova is online and ready.")

while True:
    command = listen()
    if "nova" in command:
        cmd = command.replace("nova", "").strip()
        if not cmd:
            speak("Yes?")
            cmd = listen()
        if cmd:
            process_command(cmd)
