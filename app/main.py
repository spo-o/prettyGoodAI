import os
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from dotenv import load_dotenv
import requests
from datetime import datetime
from openai import OpenAI


load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

client_openai = OpenAI()

ACTIVE_CALLS = {}

TEST_NUMBER = "+18054398008"

app = Flask(__name__)


import random
from scenarios import SCENARIOS

@app.route("/voice", methods=["POST"])
def voice():
    call_sid = request.form.get("CallSid")

    scenario = random.choice(SCENARIOS)

    ACTIVE_CALLS[call_sid] = {
        "scenario": scenario,
        "turn": 1,
        "history": []
    }

    response = VoiceResponse()

    response.say(
        "Hello, I am calling about an appointment.",
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
        return str(VoiceResponse())


    audio_url = recording_url + ".wav"

    response_audio = requests.get(
        audio_url,
        auth=(ACCOUNT_SID, AUTH_TOKEN)
    )

    os.makedirs("transcripts", exist_ok=True)
    filename = f"transcripts/{call_sid}_{int(datetime.now().timestamp())}.wav"

    with open(filename, "wb") as f:
        f.write(response_audio.content)

    # Transcribe clinic response
    with open(filename, "rb") as audio_file:
        transcript = client_openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )

    clinic_text = transcript.text
    print("Clinic said:", clinic_text)

    call_data = ACTIVE_CALLS.get(call_sid)

    if not call_data:
        return str(VoiceResponse())

    call_data["history"].append({
        "clinic": clinic_text
    })

    # Generate patient reply
    scenario = call_data["scenario"]

    prompt = f"""
    You are acting as a patient in a phone call with a clinic AI.

    Persona:
    {scenario['persona']}

    Clinic just said:
    "{clinic_text}"

    Respond naturally in one short sentence.
    """

    completion = client_openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    patient_reply = completion.choices[0].message.content
    print("Patient reply:", patient_reply)

    call_data["turn"] += 1

    response = VoiceResponse()

    if call_data["turn"] > 5:
        response.say("Thank you, goodbye.")
        response.hangup()
        ACTIVE_CALLS.pop(call_sid, None)
    else:
        response.say(patient_reply, voice="alice")
        response.record(
            action="/recording",
            method="POST",
            max_length=30
        )

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
