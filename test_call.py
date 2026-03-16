import asyncio
import sys
import os
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from twilio.rest import Client


def make_test_call():
    account_sid   = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token    = os.getenv("TWILIO_AUTH_TOKEN")
    from_number   = os.getenv("TWILIO_PHONE_NUMBER")
    to_number     = os.getenv("YOUR_PHONE_NUMBER")

    if not all([account_sid, auth_token, from_number, to_number]):
        print("❌ Missing credentials in .env")
        print("   Need: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, YOUR_PHONE_NUMBER")
        return

    client = Client(account_sid, auth_token)

    print(f"📞 Calling {to_number} from {from_number}...")

    call = client.calls.create(
        twiml="""
        <Response>
            <Say voice="Polly.Joanna">
                Hello! This is Jarvis, your autonomous AI assistant.
                I am calling to confirm your haircut appointment tomorrow afternoon
                at Style Studio on Queen Street.
                The appointment is booked for 2pm.
                Have a great day!
            </Say>
        </Response>
        """,
        to=to_number,
        from_=from_number,
    )

    print(f"✅ Call initiated!")
    print(f"   Call SID: {call.sid}")
    print(f"   Status:   {call.status}")
    print(f"   Check https://console.twilio.com for call logs")


if __name__ == "__main__":
    make_test_call()