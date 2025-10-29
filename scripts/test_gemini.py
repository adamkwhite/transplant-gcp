#!/usr/bin/env python3
"""
Test Gemini API to find working model names
"""

import sys

import google.generativeai as genai

if len(sys.argv) < 2:
    print("Usage: python test_gemini.py YOUR_API_KEY")
    sys.exit(1)

api_key = sys.argv[1]
genai.configure(api_key=api_key)

print("Testing Gemini API Models...")
print("=" * 50)

# First, list all available models
print("\nListing all available models:")
try:
    for model in genai.list_models():
        print(f"  - {model.name}")
        if "generateContent" in model.supported_generation_methods:
            print("    ✓ Supports generateContent")
except Exception as e:
    print(f"Error listing models: {e}")

print("\n" + "=" * 50)
print("\nTesting specific model names:")

# Test various model name formats
test_models = [
    "gemini-pro",
    "gemini-1.0-pro",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "models/gemini-pro",
    "models/gemini-1.0-pro",
    "models/gemini-1.5-pro",
    "models/gemini-1.5-flash",
    "gemini-pro-vision",
    "models/gemini-pro-vision",
]

for model_name in test_models:
    try:
        print(f"\nTesting: {model_name}")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say hello in 3 words")
        print(f"  ✅ SUCCESS! Response: {response.text[:50]}")
        print(f"  >>> USE THIS MODEL NAME: {model_name}")
        break  # Stop at first working model
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            print("  ❌ Not found")
        else:
            print(f"  ❌ Error: {error_msg[:100]}")

print("\n" + "=" * 50)
print("\nDONE! Use the first working model name in your code.")
