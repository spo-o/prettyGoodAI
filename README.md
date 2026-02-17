# Pretty Good AI – Automated Voice Agent Stress Testing Framework

This project implements an automated patient simulation system designed to stress test the Pretty Good AI healthcare voice agent.

The framework programmatically initiates phone calls, simulates realistic patient behaviors, records and transcribes conversations, and generates structured evaluation reports.
## Overview

This application simulates realistic patient interactions with a healthcare voice AI system.

For each call, the system:

- Initiates an outbound call using Twilio

- Simulates a patient persona using OpenAI

- Records and transcribes the clinic’s responses

- Maintains multi-turn conversation state

- Evaluates the full conversation using structured LLM analysis

- Generates transcripts and evaluation reports

The goal is to test conversational robustness, state persistence, intent handling, and safety boundaries.
## Prerequisites

- [Python 3.10+](https://www.python.org/downloads/)
- A Twilio Number with Voice Capabilities: [Instructions to purchase a number.](https://support.twilio.com/hc/en-us/articles/223180928-How-to-Buy-a-Twilio-Phone-Number)
- An Open AI Account and API Key: Visit Open AI's platform [here](https://platform.openai.com/api-keys) for more information.
- Deployed webhook endpoint (e.g., Railway)

## Installation

1.  Clone this repository
2.  Install the required dependencies:
   `pip  install  -r  requirements.txt`
3.  Create a .env file and configure the following variables:
    `TWILIO_ACCOUNT_SID=`
    `TWILIO_AUTH_TOKEN=`
    `TWILIO_PHONE_NUMBER=`
    `OPENAI_API_KEY=`

## Usage

1.  Deploy the application (Railway in this case).

2.  Ensure your Twilio outbound call webhook points to:
    `https://your-deployment-url/voice`

3.  Trigger calls programmatically using:
    `python trigger.py`
    
4.  Since the application is deployed in Railways, no need to run the Flask framework, Procfile ensures that every time there is git commit, it is deployed instantly.
    

## How It Works

1.  Twilio initiates an outbound call to the Pretty Good AI.

2.  The clinic responds.

3. Audio is recorded and downloaded.

4. Whisper transcribes the clinic’s speech.

5. GPT generates the patient’s next response based on persona.

6. Conversation continues for multiple turns.

7. Full transcript is evaluated using structured LLM prompt.

8. Transcript and evaluation report are saved.

## Project Structure

- `main.py`: The main application file containing the FastAPI server, WebSocket handler, and OpenAI integration
- `requirements.txt`: Python dependencies
- `.env`: Environment variables for API keys and configuration

## Conclusion 

This project demonstrates an automated persona-driven stress testing framework for evaluating healthcare voice AI systems under realistic conversational variability.

The framework can be extended for regression testing, automated scoring, and long-term robustness benchmarking.