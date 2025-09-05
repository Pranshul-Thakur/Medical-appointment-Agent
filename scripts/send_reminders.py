import os
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import base64
from email.mime.text import MIMEText

# --- LangChain/LangGraph specific imports ---
from langchain_google_genai import ChatGoogleGenerativeAI

# --- NEW: Imports for Google Gmail API Integration ---
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Load Environment Variables for the API Key ---
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

# --- Configuration ---
SCHEDULES_DIR = os.path.join("data", "doctor_schedules")
PATIENT_DATA_PATH = os.path.join("data", "patients.csv")
SIMULATED_TODAY_DATE = "2025-09-08" # Adjusted for testing

# --- NEW: Gmail API Configuration ---
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]

# --- AI Email Drafting Function (remains the same) ---
def draft_reminder_email(patient_name: str, appointment_date: str, appointment_time: str, reminder_type: int) -> dict:
    print(f"--- Drafting {reminder_type}-day reminder email for {patient_name} with AI ---")
    if not API_KEY: return {"subject": "Error", "body": "API key not found."}
    llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=API_KEY)
    subject = "Your Upcoming Appointment Reminder"
    prompt_template = ""
    if reminder_type == 7:
        prompt_template = f"Draft a friendly 7-day reminder email for {patient_name} about their appointment on {appointment_date} at {appointment_time}. Mention they should complete their intake form. Sign off from 'The MediCare Allergy & Wellness Center'."
    elif reminder_type == 3:
        subject = "Action Required: Please Confirm Your Appointment"
        prompt_template = f"Draft a 3-day reminder email for {patient_name} for their appointment on {appointment_date} at {appointment_time}. The tone should be slightly more urgent. Ask them to confirm their visit. Include clear options like '[Confirm Visit]' or '[Cancel Visit]'. Sign off from 'The MediCare Allergy & Wellness Center'."
    elif reminder_type == 1:
        subject = "FINAL REMINDER: Your Appointment is Tomorrow"
        prompt_template = f"Draft a final, 1-day reminder for {patient_name} about their appointment tomorrow, {appointment_date}, at {appointment_time}. The tone should be urgent but polite. Remind them again about the intake form and ask for a final confirmation. Sign off from 'The MediCare Allergy & Wellness Center'."

    try:
        response = llm.invoke(prompt_template)
        return {"subject": subject, "body": response.content}
    except Exception as e:
        print(f"Error calling LLM for email drafting: {e}")
        return {"subject": "Error", "body": "Could not draft email content."}

# --- Function to Create a Gmail Draft (remains the same) ---
def create_gmail_draft(to_email: str, subject: str, body: str):
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
        message = MIMEText(body)
        message["to"] = to_email
        message["subject"] = subject
        create_message = {"message": {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}}
        draft = service.users().drafts().create(userId="me", body=create_message).execute()
        print(f"Successfully created Gmail draft for {to_email}. Draft ID: {draft['id']}")
    except HttpError as error:
        print(f"An error occurred with the Gmail API: {error}")
    except FileNotFoundError:
        print("\n--- GMAIL API ERROR ---")
        print("Error: credentials.json not found.")
        print("---------------------\n")


def send_reminders():
    print(f"--- Running Reminder System for Simulated Date: {SIMULATED_TODAY_DATE} ---")
    try:
        patients_df = pd.read_csv(PATIENT_DATA_PATH)
    except FileNotFoundError: return print(f"Error: Patient data not found.")
    
    # ... (Logic to gather appointments remains the same) ...
    all_booked_appointments = []
    for filename in os.listdir(SCHEDULES_DIR):
        if filename.endswith(".xlsx"):
            file_path = os.path.join(SCHEDULES_DIR, filename)
            try:
                schedule_df = pd.read_excel(file_path, dtype={'Date': str, 'PatientID': str})
                booked_df = schedule_df[schedule_df['Status'].str.lower() == 'booked'].copy()
                if not booked_df.empty: all_booked_appointments.append(booked_df)
            except Exception as e: print(f"Warning: Could not process {filename}. Error: {e}")

    if not all_booked_appointments: return print("No booked appointments found.")
    
    combined_df = pd.concat(all_booked_appointments, ignore_index=True).drop_duplicates(subset=['PatientID', 'Date'])
    today = datetime.strptime(SIMULATED_TODAY_DATE, "%Y-%m-%d")
    reminders_sent_count = 0

    for _, appointment in combined_df.iterrows():
        try:
            appointment_date_obj = datetime.strptime(appointment['Date'], "%Y-%m-%d")
            days_until = (appointment_date_obj - today).days
            patient_info = patients_df[patients_df['PatientID'] == appointment['PatientID']]
            if patient_info.empty: continue

            patient_name = patient_info.iloc[0]['FirstName']
            patient_email = patient_info.iloc[0]['Email']

            # --- THE FIX: Check if the email is valid before proceeding ---
            if pd.isna(patient_email) or not isinstance(patient_email, str):
                print(f"\nWarning: Skipping reminder for {patient_name} (PatientID: {appointment['PatientID']}) because their email address is missing.")
                continue
            
            reminder_type = 0
            if days_until == 7: reminder_type = 7
            elif days_until == 3: reminder_type = 3
            elif days_until == 1: reminder_type = 1

            if reminder_type > 0:
                email_content = draft_reminder_email(patient_name, appointment['Date'], appointment['StartTime'], reminder_type)
                
                print(f"\n--- Creating Gmail Draft for {patient_email} ---")
                create_gmail_draft(patient_email, email_content["subject"], email_content["body"])
                reminders_sent_count += 1

        except Exception as e: print(f"Could not process reminder for PatientID {appointment.get('PatientID', 'N/A')}: {e}")

    if reminders_sent_count == 0: print("\nNo reminders were due to be sent for the simulated date.")
    else: print(f"\n--- Reminder System Finished: Created {reminders_sent_count} drafts. ---")


if __name__ == "__main__":
    send_reminders()