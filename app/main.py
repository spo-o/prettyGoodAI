import os
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from dotenv import load_dotenv
import requests
from datetime import datetime

load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

TEST_NUMBER = "+12405013291"

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
    call_sid = request.form.get("CallSid")

    if not recording_url:
        print("No recording URL received.")
        twiml = VoiceResponse()
        twiml.say("Goodbye.")
        return str(twiml)


    print("Recording URL:", recording_url)

    # Twilio recordings need .wav extension
    audio_url = recording_url + ".wav"

    # Download audio with Twilio auth
    response = requests.get(
        audio_url,
        auth=(ACCOUNT_SID, AUTH_TOKEN)
    )

    # Ensure transcripts folder exists
    os.makedirs("transcripts", exist_ok=True)

    filename = f"transcripts/{call_sid}_{int(datetime.now().timestamp())}.wav"

    with open(filename, "wb") as f:
        f.write(response.content)

    print("Saved recording:", filename)

    twiml = VoiceResponse()
    twiml.say("Thank you. Goodbye.")
    return str(twiml)




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
