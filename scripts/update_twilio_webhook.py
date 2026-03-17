"""
Run this after docker compose up to update Twilio with the current ngrok URL.
"""
import httpx
import time
import os
from dotenv import load_dotenv

load_dotenv()


def get_ngrok_url() -> str:
    for attempt in range(15):
        try:
            res  = httpx.get("http://localhost:4040/api/tunnels", timeout=3)
            data = res.json()
            for tunnel in data.get("tunnels", []):
                if tunnel.get("proto") == "https":
                    return tunnel["public_url"]
        except Exception:
            pass
        print(f"  Waiting for ngrok... ({attempt + 1}/15)")
        time.sleep(2)
    raise RuntimeError("Could not get ngrok URL")


def update_twilio(ngrok_url: str):
    from twilio.rest import Client

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token  = os.getenv("TWILIO_AUTH_TOKEN")
    phone_sid   = os.getenv("TWILIO_PHONE_SID")  # we'll get this below

    client = Client(account_sid, auth_token)

    # Find your Twilio phone number
    numbers = client.incoming_phone_numbers.list()
    if not numbers:
        print("No Twilio phone numbers found")
        return

    number = numbers[0]
    webhook_url = f"{ngrok_url}/voice/incoming"

    # Update the webhook
    client.incoming_phone_numbers(number.sid).update(
        voice_url=webhook_url,
        voice_method="POST",
    )

    print(f"✓ Twilio webhook updated to: {webhook_url}")
    print(f"  Phone number: {number.phone_number}")

    # Save ngrok URL to .env for the app to use
    with open(".env", "r") as f:
        lines = f.readlines()

    with open(".env", "w") as f:
        updated = False
        for line in lines:
            if line.startswith("NGROK_URL="):
                f.write(f"NGROK_URL={ngrok_url}\n")
                updated = True
            else:
                f.write(line)
        if not updated:
            f.write(f"\nNGROK_URL={ngrok_url}\n")

    print(f"✓ NGROK_URL saved to .env: {ngrok_url}")


if __name__ == "__main__":
    print("Getting ngrok URL...")
    url = get_ngrok_url()
    print(f"ngrok URL: {url}")
    update_twilio(url)
    print("\nDone! Call your Twilio number to talk to Jarvis.")