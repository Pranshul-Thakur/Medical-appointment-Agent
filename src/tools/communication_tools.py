import os
from dotenv import load_dotenv
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd

from langchain_google_genai import ChatGoogleGenerativeAI
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from langchain_core.tools import tool

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]

# --- UPDATED: The link to your new Google Form ---
GOOGLE_FORM_LINK = "https://docs.google.com/forms/d/e/1FAIpQLSfIDJA-qML8KPZKwpnFzQyQZopOrYg8cAvVKQD8Os6wRW9N6Q/viewform?usp=sharing"

def draft_confirmation_email(patient_name: str, appointment_datetime: str, doctor_name: str) -> dict:
    """Uses an LLM to draft a personalized confirmation email with the Google Form link."""
    print(f"--- Drafting confirmation email for {patient_name} with AI ---")
    if not API_KEY:
        return {"subject": "Error", "body": "API key not found."}

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=API_KEY)
    
    subject = "Your Appointment is Confirmed!"
    # UPDATED: The prompt now instructs the AI to include the Google Form link.
    prompt = f"""
    Draft a friendly and professional appointment confirmation email.
    - Patient Name: {patient_name}
    - Doctor Name: {doctor_name}
    - Appointment Date & Time: {appointment_datetime}
    - CRITICAL: You must include a call to action for the patient to fill out the New Patient Intake Form before their visit using this exact link: {GOOGLE_FORM_LINK}
    - Sign off from: "The MediCare Allergy & Wellness Center"
    """

    try:
        response = llm.invoke(prompt)
        return {"subject": subject, "body": response.content}
    except Exception as e:
        print(f"Error calling LLM for email drafting: {e}")
        return {"subject": "Error", "body": "Could not draft email content."}

def create_gmail_draft(to_email: str, subject: str, body: str):
    """Authenticates with Gmail and creates a draft."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        # We use MIMEText now since we are no longer sending attachments.
        message = MIMEText(body)
        message["to"] = to_email
        message["subject"] = subject
        
        create_message = {"message": {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}}
        draft = service.users().drafts().create(userId="me", body=create_message).execute()
        print(f"Successfully created confirmation draft for {to_email}. Draft ID: {draft['id']}")
    except (HttpError, FileNotFoundError) as error:
        print(f"An error occurred with the Gmail API: {error}")

@tool
def send_confirmation_with_form(patient_id: str, appointment_datetime: str, doctor_name: str, patient_email: str) -> str:
    """
    Drafts and creates a Gmail draft for an appointment confirmation, including a link to the intake form.
    This should be the final step after an appointment is successfully booked.
    """
    print(f"--- Sending confirmation with form for Patient ID: {patient_id} ---")
    
    # In a real app, we might look up the patient's name here from the DB.
    # For now, using the ID is sufficient for the email draft.
    patient_name = f"Patient {patient_id}"

    if pd.isna(patient_email) or not isinstance(patient_email, str):
        return "Error: Cannot send confirmation because the patient's email address is missing or invalid."

    email_content = draft_confirmation_email(patient_name, appointment_datetime, doctor_name)
    
    if "Error" in email_content["subject"]:
        return "Failed to draft the confirmation email."
        
    create_gmail_draft(patient_email, email_content["subject"], email_content["body"])
    
    return "A confirmation email with a link to the patient intake form has been drafted successfully."