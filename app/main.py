import os
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

TEST_NUMBER = "+18054398008"

app = Flask(__name__)


@app.route("/voice", methods=["POST"])
def voice():
    response = VoiceResponse()

    response.say(
        "Hello, I would like to schedule an appointment.",
        voice="alice"
    )

    response.record(
        action="/recording",
        method="POST",
        max_length=30
    )

    return str(response)


@app.route("/recording", methods=["POST"])
def recording():
    recording_url = request.form.get("RecordingUrl")
    print("Recording URL:", recording_url)

    response = VoiceResponse()
    response.say("Thank you. Goodbye.")
    return str(response)


def make_call():
    client = Client(ACCOUNT_SID, AUTH_TOKEN)

    call = client.calls.create(
        to=TEST_NUMBER,
        from_=TWILIO_PHONE_NUMBER,
        url="https://prettygoodai-production.up.railway.app/voice"

    )

    print(f"Call initiated. SID: {call.sid}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
