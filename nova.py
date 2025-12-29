import speech_recognition as sr
import pyttsx3
import os
import webbrowser
import pyautogui
import datetime
import psutil
import logging

# Configure Logging
logging.basicConfig(
    filename="nova_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

engine = pyttsx3.init()
recognizer = sr.Recognizer()

def log_interaction(entity, message):
    """Logs the interaction to the log file and prints to console."""
    log_entry = f"{entity}: {message}"
    logging.info(log_entry)
    if entity == "Nova":
        print(f"Nova: {message}")
    elif entity == "User":
        print(f"User: {message}")

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
        except Exception as e:
            return ""

def process_command(cmd):
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

    elif "time now" in cmd or "the time" in cmd:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The current time is {current_time}")

    elif "check battery" in cmd or "battery status" in cmd:
        battery = psutil.sensors_battery()
        if battery:
            percentage = battery.percent
            plugged = battery.power_plugged
            status = "plugged in" if plugged else "not plugged in"
            speak(f"Battery is at {percentage} percent and it is {status}")
        else:
            speak("Battery information is not available")

    elif "search" in cmd:
        if "search" == cmd.strip():
            speak("What should I search?")
            query = listen()
        else:
            query = cmd.replace("search", "").strip()
        
        if query:
            url = "https://www.google.com/search?q=" + query
            webbrowser.open(url)
            speak("Searching " + query)

    elif "play" in cmd:
        query = cmd.replace("play", "").strip()
        if query:
            speak(f"Playing {query}")
            webbrowser.open(f"https://www.youtube.com/results?search_query={query}")

    elif "take screenshot" in cmd:
        speak("Taking screenshot")
        screenshot = pyautogui.screenshot()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot.save(f"screenshot_{timestamp}.png")
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
        speak("Are you sure you want to shut down?")
        reply = listen()
        if "yes" in reply:
            speak("Shutting down in 5 seconds")
            os.system("shutdown /s /t 5")
        else:
            speak("Shutdown cancelled")

    elif "nova stop" in cmd or "stop nova" in cmd or "exit" in cmd:
        speak("Goodbye! Have a great day.")
        exit()

    else:
        speak("I'm not sure how to help with that yet.")

print("Nova Assistant is Starting...")
speak("Nova Assistant is online.")

while True:
    command = listen()
    if "nova" in command:
        cmd = command.replace("nova", "").strip()
        if cmd == "":
            speak("How can I help you?")
            cmd = listen()
            if cmd:
                process_command(cmd)
        else:
            process_command(cmd)
