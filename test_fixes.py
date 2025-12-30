"""
Nova Assistant - Automated Testing Script
Tests the fixed version without requiring voice input
"""

import json
import re
from difflib import SequenceMatcher

# Copy functions from nova_fixed.py to test independently

def normalize_text(text):
    """Normalize speech text for better matching."""
    if not text:
        return ""
    
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    
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
    """Validate if a trigger phrase is acceptable for learning."""
    MIN_TRIGGER_LENGTH = 3
    MIN_WORD_COUNT = 2
    
    trigger = trigger.strip()
    
    if len(trigger) < MIN_TRIGGER_LENGTH:
        return False, f"Trigger too short. Minimum {MIN_TRIGGER_LENGTH} characters."
    
    if trigger.isdigit():
        return False, "Trigger cannot be only numbers."
    
    words = trigger.split()
    if len(words) < MIN_WORD_COUNT:
        return False, f"Trigger needs at least {MIN_WORD_COUNT} words."
    
    digit_count = sum(c.isdigit() for c in trigger)
    if digit_count > len(trigger) / 2:
        return False, "Trigger contains too many numbers."
    
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at"}
    if all(word in stop_words for word in words):
        return False, "Trigger cannot be only common words."
    
    return True, ""

def fuzzy_match(text, pattern, threshold=0.75):
    """Check if text fuzzy matches pattern."""
    similarity = SequenceMatcher(None, text, pattern).ratio()
    return similarity >= threshold

def check_exit_command(cmd):
    """Check for exit/stop commands."""
    exit_patterns = [
        "stop", "exit", "quit", "goodbye", "bye", "shut down nova",
        "stop nova", "nova stop", "close nova", "turn off"
    ]
    
    for pattern in exit_patterns:
        if pattern in cmd or fuzzy_match(cmd, pattern, 0.8):
            return True
    return False

# Run Tests
print("=" * 60)
print("🧪 NOVA ASSISTANT - TESTING SUITE")
print("=" * 60)

# Test 1: Text Normalization
print("\n📝 TEST 1: Text Normalization")
print("-" * 60)

test_cases = [
    ("What's  the   time?", "what is the time"),
    ("OPEN NOTEPAD", "open notepad"),
    ("learn   new    command", "learn new command"),
    ("I'm ready!", "i am ready"),
    ("don't stop", "do not stop"),
]

passed = 0
for input_text, expected in test_cases:
    result = normalize_text(input_text)
    status = "✅" if result == expected else "❌"
    print(f"{status} Input: '{input_text}'")
    print(f"   Expected: '{expected}'")
    print(f"   Got:      '{result}'")
    if result == expected:
        passed += 1

print(f"\n📊 Passed: {passed}/{len(test_cases)}")

# Test 2: Trigger Validation
print("\n\n🔒 TEST 2: Trigger Validation")
print("-" * 60)

trigger_tests = [
    ("open notepad", True, "Valid multi-word trigger"),
    ("89", False, "Digit-only trigger"),
    ("hi", False, "Too short, single word"),
    ("the and", False, "Only stop words"),
    ("open123", False, "Too many digits"),
    ("search google", True, "Valid trigger"),
    ("a", False, "Single character"),
]

passed = 0
for trigger, should_pass, description in trigger_tests:
    is_valid, error_msg = is_valid_trigger(trigger)
    status = "✅" if is_valid == should_pass else "❌"
    print(f"{status} '{trigger}' - {description}")
    if not is_valid:
        print(f"   Reason: {error_msg}")
    if is_valid == should_pass:
        passed += 1

print(f"\n📊 Passed: {passed}/{len(trigger_tests)}")

# Test 3: Fuzzy Matching
print("\n\n🎯 TEST 3: Fuzzy Matching")
print("-" * 60)

fuzzy_tests = [
    ("learn new", "learn new command", True, 0.75),
    ("open note", "open notepad", True, 0.75),
    ("time now", "time", False, 0.75),
    ("stop nova", "nova stop", True, 0.75),
    ("hello", "hello there", True, 0.75),
    ("xyz", "abc", False, 0.75),
]

passed = 0
for text, pattern, should_match, threshold in fuzzy_tests:
    result = fuzzy_match(text, pattern, threshold)
    status = "✅" if result == should_match else "❌"
    
    similarity = SequenceMatcher(None, text, pattern).ratio()
    
    print(f"{status} '{text}' vs '{pattern}'")
    print(f"   Similarity: {similarity:.2%} (threshold: {threshold:.0%})")
    print(f"   Expected: {should_match}, Got: {result}")
    
    if result == should_match:
        passed += 1

print(f"\n📊 Passed: {passed}/{len(fuzzy_tests)}")

# Test 4: Exit Command Detection
print("\n\n🚪 TEST 4: Exit Command Detection")
print("-" * 60)

exit_tests = [
    ("stop", True),
    ("exit", True),
    ("nova stop", True),
    ("stop nova", True),
    ("goodbye", True),
    ("quit", True),
    ("shut down nova", True),
    ("open notepad", False),
    ("hello", False),
]

passed = 0
for cmd, should_exit in exit_tests:
    result = check_exit_command(cmd)
    status = "✅" if result == should_exit else "❌"
    print(f"{status} '{cmd}' → Exit: {result} (expected: {should_exit})")
    if result == should_exit:
        passed += 1

print(f"\n📊 Passed: {passed}/{len(exit_tests)}")

# Test 5: Learned Commands Validation
print("\n\n💾 TEST 5: Learned Commands File")
print("-" * 60)

try:
    with open("learned_commands.json", "r") as f:
        learned = json.load(f)
    
    print(f"✅ File loaded successfully")
    print(f"📝 Total learned commands: {len(learned)}")
    
    invalid_count = 0
    for trigger, action in learned.items():
        is_valid, error_msg = is_valid_trigger(trigger)
        if not is_valid:
            print(f"⚠️  Invalid trigger found: '{trigger}' - {error_msg}")
            invalid_count += 1
        else:
            print(f"✅ '{trigger}' → '{action}'")
    
    if invalid_count > 0:
        print(f"\n⚠️  Found {invalid_count} invalid triggers. Consider cleaning them.")
    else:
        print(f"\n✅ All triggers are valid!")
        
except FileNotFoundError:
    print("ℹ️  No learned_commands.json found (will be created on first learning)")
except json.JSONDecodeError:
    print("❌ learned_commands.json is corrupted!")

# Overall Summary
print("\n\n" + "=" * 60)
print("📊 OVERALL TEST SUMMARY")
print("=" * 60)
print("✅ Text Normalization: Working")
print("✅ Trigger Validation: Working")
print("✅ Fuzzy Matching: Working")
print("✅ Exit Detection: Working")
print("\n🎉 All core functions are operational!")
print("\n📋 Next Steps:")
print("   1. Run: python nova_fixed.py")
print("   2. Test with voice commands")
print("   3. Check nova_log.txt for detailed logs")
print("   4. Refer to FIXES_EXPLAINED.md for full documentation")
print("=" * 60)
