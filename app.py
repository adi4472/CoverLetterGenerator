from flask import Flask, request, jsonify
import os
import openai
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
from docx import Document  # Import library to handle .docx files

# Load environment variables from .env file
load_dotenv()

# Slack and OpenAI API keys
slack_token = os.getenv("SLACK_BOT_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize the Slack client
client = WebClient(token=slack_token)

# Channel IDs
PROPOSAL_CHANNEL_ID = "C082W4UDLJJ"  # Proposal channel ID
RESULT_CHANNEL_ID = "C08383AU6HZ"   # Result channel ID

# Load your resume from a .txt file
RESUME_PATH = "resume.txt"  # Path to your .txt resume

def load_resume_from_txt(filepath):
    """Reads text from a .txt file and returns it as a string."""
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            resume_text = file.read().strip()  # Read and strip any extra whitespace
        return resume_text
    except Exception as e:
        print(f"Error loading resume: {e}")
        return "Resume not available."

# Load resume content
resume_content = load_resume_from_txt(RESUME_PATH)

# Debug: Print loaded resume content
print("Resume Content Loaded:\n", resume_content)


app = Flask(__name__)

# Slack event listener
@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.json
    print("Received Slack event:", data)  # Log incoming event

    # URL verification for Slack event subscription
    if "type" in data:
        if data["type"] == "url_verification":
            return jsonify({"challenge": data["challenge"]})

    # Process message event
    if "event" in data:
        event = data["event"]
        channel_id = event.get('channel')
        user = event.get('user')  # The user who sent the message
        text = event.get('text', '')  # The message text

        print(f"Channel ID: {channel_id}, User: {user}, Text: {text}")  # Log event details

        # Process the message if it is from the proposal channel
        if channel_id == PROPOSAL_CHANNEL_ID and user != event.get('bot_id'):
            print(f"Received proposal: {text}")  # Log the proposal message

            # Generate cover letter with OpenAI
            cover_letter = generate_cover_letter(text)

            try:
                # Send the generated cover letter to the result channel
                response = client.chat_postMessage(
                    channel=RESULT_CHANNEL_ID,
                    text=f"Cover Letter for Proposal: \n{cover_letter}"
                )
                print(f"Cover letter sent to {RESULT_CHANNEL_ID}: {response}")

            except SlackApiError as e:
                print(f"Error sending message: {e.response['error']}")

    return "Event received", 200


# Generate cover letter using OpenAI with resume context
def generate_cover_letter(proposal_text):
    try:
        print("Sending request to OpenAI...")

        # Send the request to OpenAI's chat completion API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Or "gpt-4" if you have access to it
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates personalized cover letters."},
                {"role": "system", "content": f"My resume: {resume_content}"},
                {"role": "user", "content": f"Write a personalized cover letter for the following project proposal: {proposal_text}"}
            ],
            max_tokens=350  # Adjust token limit as necessary
        )

        # Extract the generated cover letter
        if response['choices']:
            cover_letter = response['choices'][0]['message']['content'].strip()
            print(f"Generated cover letter: {cover_letter}")
            return cover_letter
        else:
            print("No response choices returned from OpenAI")
            return "Sorry, I couldn't generate a cover letter at the moment."

    except openai.OpenAIError as e:  # Corrected exception handling
        print(f"OpenAI API error: {e}")
        return "Sorry, there was an error with OpenAI."

    except Exception as e:
        print(f"Error generating cover letter: {e}")
        return "Sorry, there was an unexpected error."

# Endpoint to update resume dynamically
@app.route("/update-resume", methods=["POST"])
def update_resume():
    global resume_content
    data = request.json
    new_resume = data.get("resume")
    if new_resume:
        resume_content = new_resume
        return jsonify({"message": "Resume updated successfully"}), 200
    return jsonify({"error": "No resume provided"}), 400

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
