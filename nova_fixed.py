import speech_recognition as sr
import pyttsx3
import os
import webbrowser
import pyautogui
import datetime
import psutil
import logging
import json
import re
from difflib import SequenceMatcher

# ---------------- CONFIG ----------------

COMMANDS_FILE = "learned_commands.json"

# Recognition settings
MIN_TRIGGER_LENGTH = 3  # Minimum characters for a trigger
MIN_WORD_COUNT = 2      # Minimum words for learning triggers
PHRASE_TIME_LIMIT = 5   # Max seconds to listen for a phrase
PAUSE_THRESHOLD = 0.8   # Seconds of silence to consider phrase complete
ENERGY_THRESHOLD = 300  # Minimum audio energy to consider as speech
SIMILARITY_THRESHOLD = 0.75  # Fuzzy match threshold (0-1)

logging.basicConfig(
    filename="nova_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

engine = pyttsx3.init()
recognizer = sr.Recognizer()

# Optimize recognizer settings
recognizer.energy_threshold = ENERGY_THRESHOLD
recognizer.pause_threshold = PAUSE_THRESHOLD
recognizer.dynamic_energy_threshold = True

# ---------------- UTILITIES ----------------

def log_interaction(entity, message):
    logging.info(f"{entity}: {message}")
    print(f"{entity}: {message}")

def speak(text):
    log_interaction("Nova", text)
    engine.say(text)
    engine.runAndWait()

def normalize_text(text):
    """
    Normalize speech text for better matching.
    - Convert to lowercase
    - Remove extra whitespace
    - Remove punctuation
    - Standardize common variations
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower().strip()
    
    # Remove punctuation except spaces
    text = re.sub(r'[^\w\s]', '', text)
    
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Common speech-to-text corrections
    replacements = {
        "whats": "what is",
        "wheres": "where is",
        "hows": "how is",
        "im": "i am",
        "youre": "you are",
        "dont": "do not",
        "cant": "can not",
        "wont": "will not",
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text.strip()

def is_valid_trigger(trigger):
    """
    Validate if a trigger phrase is acceptable for learning.
    Returns (is_valid, error_message)
    """
    trigger = trigger.strip()
    
    # Check minimum length
    if len(trigger) < MIN_TRIGGER_LENGTH:
        return False, f"Trigger too short. Minimum {MIN_TRIGGER_LENGTH} characters."
    
    # Check for digits only
    if trigger.isdigit():
        return False, "Trigger cannot be only numbers."
    
    # Check word count
    words = trigger.split()
    if len(words) < MIN_WORD_COUNT:
        return False, f"Trigger needs at least {MIN_WORD_COUNT} words."
    
    # Check for mostly numbers
    digit_count = sum(c.isdigit() for c in trigger)
    if digit_count > len(trigger) / 2:
        return False, "Trigger contains too many numbers."
    
    # Check for common stop words only
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at"}
    if all(word in stop_words for word in words):
        return False, "Trigger cannot be only common words."
    
    return True, ""

def fuzzy_match(text, pattern, threshold=SIMILARITY_THRESHOLD):
    """
    Check if text fuzzy matches pattern using sequence matching.
    Returns True if similarity >= threshold.
    """
    similarity = SequenceMatcher(None, text, pattern).ratio()
    return similarity >= threshold

def listen():
    """
    Enhanced listening with better error handling and timeout.
    """
    with sr.Microphone() as source:
        print("\n🎤 Listening...")
        
        # Only adjust for ambient noise on first call (cached)
        if not hasattr(listen, 'calibrated'):
            print("📊 Calibrating for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            listen.calibrated = True
        
        try:
            # Listen with timeout and phrase time limit
            audio = recognizer.listen(
                source, 
                timeout=10,  # Wait max 10s for speech to start
                phrase_time_limit=PHRASE_TIME_LIMIT
            )
            
            # Recognize with Google
            text = recognizer.recognize_google(audio)
            normalized = normalize_text(text)
            
            log_interaction("User (raw)", text)
            if normalized != text.lower():
                log_interaction("User (normalized)", normalized)
            
            return normalized
            
        except sr.WaitTimeoutError:
            log_interaction("System", "Listening timeout - no speech detected")
            return ""
        except sr.UnknownValueError:
            log_interaction("System", "Could not understand audio")
            return ""
        except sr.RequestError as e:
            log_interaction("System", f"Recognition service error: {e}")
            speak("Sorry, my speech recognition service is unavailable.")
            return ""
        except Exception as e:
            log_interaction("System", f"Unexpected error: {e}")
            return ""

# ---------------- LEARNING MODE ----------------

def load_learned_commands():
    if not os.path.exists(COMMANDS_FILE):
        return {}
    try:
        with open(COMMANDS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        log_interaction("System", "Error loading learned commands - file corrupted")
        return {}

def save_learned_commands(commands):
    with open(COMMANDS_FILE, "w") as f:
        json.dump(commands, f, indent=4)

learned_commands = load_learned_commands()

def learning_mode():
    """
    Enhanced learning mode with validation.
    """
    speak("Learning mode activated. What trigger phrase should I listen for?")
    trigger = listen()

    if not trigger:
        speak("I didn't hear a trigger phrase.")
        return
    
    # Validate trigger
    is_valid, error_msg = is_valid_trigger(trigger)
    if not is_valid:
        speak(f"Invalid trigger. {error_msg}")
        log_interaction("System", f"Learning rejected: {error_msg}")
        return

    speak(f"Got it. When you say {trigger}, what action should I perform?")
    action = listen()

    if not action:
        speak("I didn't hear the action.")
        return
    
    # Check if action looks like a path or URL
    if not (action.startswith("http") or action.endswith(".exe") or "\\" in action):
        speak("The action should be a program path or web URL. For example, C:\\Windows\\System32\\notepad.exe")
        return

    # Store the command
    learned_commands[trigger] = action
    save_learned_commands(learned_commands)

    speak(f"Perfect! I have learned that {trigger} means {action}")
    log_interaction("System", f"Learned: '{trigger}' -> '{action}'")

# ---------------- COMMAND PROCESSOR ----------------

def check_exit_command(cmd):
    """
    Check for exit/stop commands with multiple variations.
    """
    exit_patterns = [
        "stop", "exit", "quit", "goodbye", "bye", "shut down nova",
        "stop nova", "nova stop", "close nova", "turn off"
    ]
    
    for pattern in exit_patterns:
        if pattern in cmd or fuzzy_match(cmd, pattern, 0.8):
            return True
    return False

def process_command(cmd):
    """
    Enhanced command processing with fuzzy matching.
    """
    cmd = normalize_text(cmd)
    
    # --- Exit Commands (highest priority) ---
    if check_exit_command(cmd):
        speak("Goodbye")
        exit()
    
    # --- Learning Mode ---
    learning_triggers = ["learn new command", "learning mode", "teach you", "learn something"]
    for trigger in learning_triggers:
        if trigger in cmd or fuzzy_match(cmd, trigger):
            learning_mode()
            return

    # --- Learned Commands (check with fuzzy matching) ---
    for trigger, action in learned_commands.items():
        if trigger in cmd or fuzzy_match(cmd, trigger):
            speak(f"Executing learned command")
            log_interaction("System", f"Matched learned command: '{trigger}'")
            try:
                if action.startswith("http"):
                    webbrowser.open(action)
                else:
                    os.startfile(action)
            except Exception as e:
                speak("Sorry, I couldn't execute that command.")
                log_interaction("System", f"Execution error: {e}")
            return

    # --- Built-in Commands ---
    
    # Greetings
    if any(word in cmd for word in ["hello", "hi", "hey"]):
        speak("Hello! How can I help you?")
    
    # Time
    elif "time" in cmd:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {current_time}")
    
    # Date
    elif "date" in cmd or "today" in cmd:
        current_date = datetime.datetime.now().strftime("%B %d, %Y")
        speak(f"Today is {current_date}")

    # Open Chrome
    elif "chrome" in cmd and "open" in cmd:
        speak("Opening Chrome")
        try:
            os.startfile("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
        except:
            speak("Chrome not found at default location")

    # Open Spotify
    elif "spotify" in cmd and "open" in cmd:
        speak("Opening Spotify")
        try:
            os.system("start spotify")
        except:
            webbrowser.open("https://open.spotify.com")

    # Open Gmail
    elif ("gmail" in cmd or "email" in cmd) and ("open" in cmd or "write" in cmd):
        speak("Opening Gmail")
        webbrowser.open("https://mail.google.com")

    # Battery
    elif "battery" in cmd:
        battery = psutil.sensors_battery()
        if battery:
            status = "plugged in" if battery.power_plugged else "not plugged in"
            speak(f"Battery is at {battery.percent} percent and {status}")
        else:
            speak("Battery info unavailable")

    # Search
    elif "search" in cmd or "google" in cmd:
        query = cmd.replace("search", "").replace("google", "").strip()
        if not query or len(query) < 2:
            speak("What should I search for?")
            query = listen()
        if query:
            webbrowser.open(f"https://www.google.com/search?q={query}")
            speak(f"Searching for {query}")

    # Play (YouTube)
    elif "play" in cmd:
        query = cmd.replace("play", "").strip()
        if query and len(query) > 1:
            webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
            speak(f"Playing {query}")
        else:
            speak("What should I play?")

    # Screenshot
    elif "screenshot" in cmd or "screen shot" in cmd:
        speak("Taking screenshot")
        img = pyautogui.screenshot()
        filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        img.save(filename)
        speak("Screenshot saved")

    # Volume controls
    elif "volume up" in cmd or "increase volume" in cmd:
        pyautogui.press("volumeup")
        speak("Volume increased")

    elif "volume down" in cmd or "decrease volume" in cmd:
        pyautogui.press("volumedown")
        speak("Volume decreased")

    elif "mute" in cmd or "unmute" in cmd:
        pyautogui.press("volumemute")

    # Window controls
    elif "close window" in cmd or "close this" in cmd:
        pyautogui.hotkey("alt", "f4")

    # Shutdown
    elif "shutdown" in cmd or "shut down" in cmd:
        speak("Are you sure you want to shut down?")
        confirmation = listen()
        if "yes" in confirmation or "sure" in confirmation or "ok" in confirmation:
            speak("Shutting down in 5 seconds")
            os.system("shutdown /s /t 5")
        else:
            speak("Shutdown cancelled")

    # Unknown command
    else:
        speak("I don't know that command yet. You can teach me by saying learn new command.")

# ---------------- MAIN LOOP ----------------

print("=" * 50)
print("🚀 Nova Assistant Starting...")
print("=" * 50)
speak("Nova is online and ready.")

while True:
    try:
        command = listen()
        
        if not command:
            continue
        
        # Check if command contains wake word "nova"
        if "nova" in command:
            # Remove wake word and process
            cmd = command.replace("nova", "").strip()
            
            if not cmd:
                speak("Yes?")
                cmd = listen()
            
            if cmd:
                process_command(cmd)
        else:
            # If no wake word, check if it's a direct command (for convenience)
            # This allows "exit" without saying "nova" first
            if check_exit_command(command):
                speak("Goodbye")
                break
                
    except KeyboardInterrupt:
        speak("Shutting down")
        log_interaction("System", "Shutdown via keyboard interrupt")
        break
    except Exception as e:
        log_interaction("System", f"Main loop error: {e}")
        continue
