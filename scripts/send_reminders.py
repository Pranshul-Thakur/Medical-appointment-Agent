import os
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import base64
from email.mime.text import MIMEText

from langchain_google_genai import ChatGoogleGenerativeAI
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

# --- Configuration ---
DB_PATH = os.path.join("data", "clinic.db")
# Change this date to test the reminder logic for different days
SIMULATED_TODAY_DATE = "2025-09-01" 
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]

def draft_reminder_email(patient_name: str, appointment_datetime: str, reminder_type: int) -> dict:
    print(f"--- Drafting {reminder_type}-day reminder email for {patient_name} with AI ---")
    if not API_KEY: return {"subject": "Error", "body": "API key not found."}
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=API_KEY)
    dt_obj = datetime.strptime(appointment_datetime, "%Y-%m-%d %H:%M")
    date_str = dt_obj.strftime("%Y-%m-%d")
    time_str = dt_obj.strftime("%H:%M")
    
    subject = "Your Upcoming Appointment Reminder"
    prompt_template = ""
    if reminder_type == 7:
        prompt_template = f"Draft a friendly 7-day reminder email for {patient_name} about their appointment on {date_str} at {time_str}. Mention they should complete their intake form. Sign off from 'The MediCare Allergy & Wellness Center'."
    elif reminder_type == 3:
        subject = "Action Required: Please Confirm Your Appointment"
        prompt_template = f"Draft a 3-day reminder email for {patient_name} for their appointment on {date_str} at {time_str}. The tone should be slightly more urgent. Ask them to confirm their visit. Include clear options like '[Confirm Visit]' or '[Cancel Visit]'. Sign off from 'The MediCare Allergy & Wellness Center'."
    elif reminder_type == 1:
        subject = "FINAL REMINDER: Your Appointment is Tomorrow"
        prompt_template = f"Draft a final, 1-day reminder for {patient_name} about their appointment tomorrow, {date_str}, at {time_str}. The tone should be urgent but polite. Remind them again about the intake form and ask for a final confirmation. Sign off from 'The MediCare Allergy & Wellness Center'."

    try:
        response = llm.invoke(prompt_template)
        return {"subject": subject, "body": response.content}
    except Exception as e:
        print(f"Error calling LLM for email drafting: {e}")
        return {"subject": "Error", "body": "Could not draft email content."}

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
    if not os.path.exists(DB_PATH):
        return print(f"Error: Database not found at {DB_PATH}")

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        query = """
        SELECT
            p.first_name,
            p.email,
            p.phone_number,
            a.appointment_datetime
        FROM
            appointments a
        JOIN
            patients p ON a.patient_id = p.patient_id;
        """
        appointments_df = pd.read_sql_query(query, conn)
    except (sqlite3.Error, pd.errors.DatabaseError) as e:
        return print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

    if appointments_df.empty:
        return print("No booked appointments found in the database.")

    today = datetime.strptime(SIMULATED_TODAY_DATE, "%Y-%m-%d")
    reminders_sent_count = 0

    for _, appointment in appointments_df.iterrows():
        try:
            patient_email = appointment['email']
            if pd.isna(patient_email) or not isinstance(patient_email, str):
                print(f"\nWarning: Skipping reminder for {appointment['first_name']} because their email is missing.")
                continue

            appointment_date_obj = datetime.strptime(appointment['appointment_datetime'], "%Y-%m-%d %H:%M")
            days_until = (appointment_date_obj.date() - today.date()).days
            
            reminder_type = 0
            if days_until == 7: reminder_type = 7
            elif days_until == 3: reminder_type = 3
            elif days_until == 1: reminder_type = 1

            if reminder_type > 0:
                email_content = draft_reminder_email(
                    appointment['first_name'], 
                    appointment['appointment_datetime'], 
                    reminder_type
                )
                
                print(f"\n--- Creating Gmail Draft for {patient_email} ---")
                create_gmail_draft(patient_email, email_content["subject"], email_content["body"])
                reminders_sent_count += 1

        except Exception as e:
            print(f"Could not process reminder for {appointment.get('first_name', 'N/A')}: {e}")

    if reminders_sent_count == 0:
        print("\nNo reminders were due to be sent for the simulated date.")
    else:
        print(f"\n--- Reminder System Finished: Created {reminders_sent_count} drafts. ---")

if __name__ == "__main__":
    send_reminders()