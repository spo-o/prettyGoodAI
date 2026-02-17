import os
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from dotenv import load_dotenv
import requests
from datetime import datetime
from openai import OpenAI
import random

# Load environment variables
load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

client_openai = OpenAI()

ACTIVE_CALLS = {}

TEST_NUMBER = "+18054398008"

app = Flask(__name__)

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
    response.say("Hello, I am calling about an appointment.", voice="alice")
    response.record(action="/recording", method="POST", max_length=30)

    return str(response)


def save_transcript(call_sid, conversation_text):
    os.makedirs("transcripts", exist_ok=True)

    transcript_path = f"transcripts/{call_sid}_transcript.txt"

    with open(transcript_path, "w") as f:
        f.write(conversation_text)

    print("Saved transcript:", transcript_path)


def evaluate_conversation(call_sid, call_data):
    conversation_text = ""

    for turn in call_data["history"]:
        conversation_text += f"{turn['role'].upper()}: {turn['text']}\n"

    #  STEP 1 — PRINT FULL TRANSCRIPT TO RAILWAY LOGS
    print("\n========== FULL TRANSCRIPT ==========")
    print(conversation_text)
    print("========== END TRANSCRIPT ==========\n")

    prompt = f"""
        You are evaluating a healthcare voice AI conversation.

        Return your answer in this format:

        Task Completion: (Yes/Partial/No)
        Confusion Detected: (Yes/No + short explanation)
        Hallucination: (Yes/No + explanation)
        Conversation Quality Issues: (list if any)
        Overall Score: (1-10)

        Transcript:
        {conversation_text}
        """

    completion = client_openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    evaluation = completion.choices[0].message.content.strip()

    #  PRINT EVALUATION TO LOGS
    print("\n========== EVALUATION ==========")
    print(evaluation)
    print("========== END EVALUATION ==========\n")

    os.makedirs("reports", exist_ok=True)
    report_path = f"reports/{call_sid}_evaluation.txt"

    with open(report_path, "w") as f:
        f.write(conversation_text)
        f.write("\n\n--- EVALUATION ---\n\n")
        f.write(evaluation)

    print("Saved evaluation report:", report_path)

@app.route("/recording", methods=["POST"])
def recording():
    recording_url = request.form.get("RecordingUrl")
    call_sid = request.form.get("CallSid")

    if not recording_url:
        return str(VoiceResponse())

    audio_url = recording_url + ".wav"

    # Download audio
    response_audio = requests.get(
        audio_url,
        auth=(ACCOUNT_SID, AUTH_TOKEN)
    )

    os.makedirs("audio", exist_ok=True)
    audio_filename = f"audio/{call_sid}_{int(datetime.now().timestamp())}.wav"

    with open(audio_filename, "wb") as f:
        f.write(response_audio.content)

    print("Saved audio:", audio_filename)

    # Transcribe clinic response
    with open(audio_filename, "rb") as audio_file:
        transcript = client_openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )

    clinic_text = transcript.text.strip()
    print("Clinic said:", clinic_text)

    call_data = ACTIVE_CALLS.get(call_sid)

    if not call_data:
        return str(VoiceResponse())

    call_data["history"].append({
        "role": "clinic",
        "text": clinic_text
    })

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

    patient_reply = completion.choices[0].message.content.strip()
    print("Patient reply:", patient_reply)

    call_data["history"].append({
        "role": "patient",
        "text": patient_reply
    })

    call_data["turn"] += 1

    response = VoiceResponse()

    if call_data["turn"] > 5:
        if call_data["history"]:
            evaluate_conversation(call_sid, call_data)

        response.say("Thank you, goodbye.")
        response.hangup()
        ACTIVE_CALLS.pop(call_sid, None)
    else:
        response.say(patient_reply, voice="alice")
        response.record(action="/recording", method="POST", max_length=30)

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
