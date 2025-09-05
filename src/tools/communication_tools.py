# This file contains tools for handling patient communication, like sending emails.

from langchain_core.tools import tool
import pandas as pd
import os

# Define the path to the patient data
PATIENT_DATA_PATH = os.path.join('data', 'patients.csv')

@tool
def send_confirmation_email(patient_id: str, appointment_date: str, appointment_time: str, doctor_name: str) -> str:
    """
    Simulates sending a confirmation email to a patient with their appointment details and a link to the intake form.

    Args:
        patient_id: The unique ID of the patient.
        appointment_date: The date of the appointment.
        appointment_time: The time of the appointment.
        doctor_name: The name of the doctor for the appointment.

    Returns:
        A string confirming that the email has been sent.
    """
    print(f"--- Running send_confirmation_email for {patient_id} ---")
    
    try:
        # Look up the patient's email address
        patients_df = pd.read_csv(PATIENT_DATA_PATH)
        patient_info = patients_df[patients_df['PatientID'] == patient_id]

        if patient_info.empty:
            return f"Error: Could not find patient with ID {patient_id} to send email."

        patient_email = patient_info.iloc[0]['Email']
        patient_name = patient_info.iloc[0]['FirstName']

        # Simulate the email content
        email_subject = "Your Appointment Confirmation"
        email_body = f"""
Dear {patient_name},

This email confirms your upcoming appointment with {doctor_name}.

Date: {appointment_date}
Time: {appointment_time}

As a next step, please complete our patient intake form before your visit. You can find the form here: [link_to_patient_intake_form.html]

We look forward to seeing you.

Sincerely,
The MediCare Allergy & Wellness Center
"""

        print("\n--- SIMULATING EMAIL ---")
        print(f"To: {patient_email}")
        print(f"Subject: {email_subject}")
        print(email_body)
        print("--- EMAIL SIMULATION END ---\n")

        return "Confirmation email has been successfully sent to the patient."
        
    except Exception as e:
        return f"An error occurred while trying to send the confirmation email: {e}"