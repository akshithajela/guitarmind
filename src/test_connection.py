"""
GuitarMind — Week 1 connection test.
Confirms the environment is set up and we can reach the Claude API.
Run:  python src/test_connection.py
"""

import os
import sys
from dotenv import load_dotenv
import anthropic

# 1. Load the API key from the .env file (never hardcode it).
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    sys.exit(
        "ERROR: ANTHROPIC_API_KEY not found.\n"
        "Fix: copy .env.example to .env and paste your real key into it."
    )

if not api_key.startswith("sk-ant-"):
    sys.exit(
        "ERROR: that doesn't look like an Anthropic key (should start with 'sk-ant-').\n"
        "Fix: re-copy the key from console.anthropic.com."
    )

# 2. Create the client.
client = anthropic.Anthropic(api_key=api_key)

# 3. Make one bare call with a GuitarMind-flavored task.
print("Calling Claude... (this confirms the connection)\n")

try:
    message = client.messages.create(
        # Sonnet 4.6 is the right default for GuitarMind: strong reasoning at
        # lower cost than Opus. Swap to "claude-opus-4-8" for max reasoning.
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=(
            "You are GuitarMind, a friendly guitar mentor. "
            "Answer briefly and name real chords."
        ),
        messages=[
            {
                "role": "user",
                "content": "Suggest a simple 4-chord progression in G major "
                           "that feels warm and hopeful. One sentence of why.",
            }
        ],
    )
    print("SUCCESS — Claude responded:\n")
    print(message.content[0].text)
    print("\nConnection confirmed. Week 1 milestone complete.")

except anthropic.AuthenticationError:
    sys.exit("\nERROR: key rejected. Check the key is correct and active.")
except anthropic.RateLimitError:
    sys.exit("\nERROR: rate limited or out of credit. Add a little credit under Billing.")
except Exception as e:
    sys.exit(f"\nERROR: unexpected problem: {e}")