import os
import pandas as pd
from langchain_core.tools import tool

# --- Tool Definitions ---

@tool
def check_availability(doctor_name: str) -> str:
    """
    Checks the schedule for a specific doctor to find available appointment slots.

    Args:
        doctor_name: The full name of the doctor (e.g., "Dr. Evelyn Reed").

    Returns:
        A string listing available dates and times, or a message if the doctor is not found or has no availability.
    """
    print(f"--- Running Availability Check for {doctor_name} ---")
    
    doctor_name_slug = doctor_name.replace(" ", "_").replace(".", "").lower()
    file_path = os.path.join("data", "doctor_schedules", f"{doctor_name_slug}_schedule.xlsx")

    if not os.path.exists(file_path):
        return f"Schedule for {doctor_name} not found. Please check the name. Available doctors are Dr. Evelyn Reed, Dr. Ben Carter, and Dr. Olivia Chen."

    try:
        schedule_df = pd.read_excel(file_path, dtype={'StartTime': str, 'EndTime': str})
        available_slots = schedule_df[schedule_df['Status'].str.lower() == 'available']

        if available_slots.empty:
            return f"No available appointments found for {doctor_name}."

        availability_str = f"Happy to help you with that. Here are the available slots for {doctor_name}:\n"
        for date, group in available_slots.groupby('Date'):
            availability_str += f"- On {date}:\n"
            times = ", ".join(sorted(group['StartTime']))
            availability_str += f"  {times}\n"
        
        return availability_str.strip()

    except Exception as e:
        return f"An error occurred while checking the schedule for {doctor_name}: {e}"

@tool
def book_appointment(doctor_name: str, appointment_date: str, appointment_time: str, patient_id: str, patient_status: str) -> str:
    """
    Books an appointment for a patient with a specific doctor at a given date and time.

    Args:
        doctor_name: The full name of the doctor (e.g., "Dr. Evelyn Reed").
        appointment_date: The date of the appointment in YYYY-MM-DD format.
        appointment_time: The start time of the appointment in HH:MM format (24-hour clock).
        patient_id: The unique ID of the patient (e.g., "PAT0051").
        patient_status: The patient's status, either "new patient" or "returning patient".

    Returns:
        A string confirming the booking or providing an error message.
    """
    print(f"--- Running Appointment Booking for {patient_id} with {doctor_name} ---")
    doctor_name_slug = doctor_name.replace(" ", "_").replace(".", "").lower()
    file_path = os.path.join("data", "doctor_schedules", f"{doctor_name_slug}_schedule.xlsx")

    if not os.path.exists(file_path):
        return f"Schedule for {doctor_name} not found. Cannot book appointment."

    try:
        schedule_df = pd.read_excel(file_path, dtype={'StartTime': str, 'EndTime': str})
        
        duration = 60 if "new" in patient_status.lower() else 30
        appt_type = "New Patient" if duration == 60 else "Returning Patient"
        num_slots_to_book = 2 if duration == 60 else 1

        target_indices = schedule_df[
            (schedule_df['Date'] == appointment_date) &
            (schedule_df['StartTime'] == appointment_time)
        ].index

        if target_indices.empty:
            return f"The requested time slot ({appointment_time} on {appointment_date}) is not in the schedule."

        start_index = target_indices[0]
        
        # Check if all required consecutive slots are available
        for i in range(num_slots_to_book):
            slot_index = start_index + i
            if slot_index >= len(schedule_df) or schedule_df.loc[slot_index, 'Status'].lower() != 'available':
                return f"Cannot book a {duration}-minute appointment at {appointment_time}. Not enough consecutive slots are available."

        # Book the slots
        for i in range(num_slots_to_book):
            slot_index = start_index + i
            schedule_df.loc[slot_index, 'Status'] = 'Booked'
            schedule_df.loc[slot_index, 'PatientID'] = patient_id
            schedule_df.loc[slot_index, 'AppointmentType'] = appt_type

        schedule_df.to_excel(file_path, index=False)
        return f"Appointment successfully booked for PatientID {patient_id} with {doctor_name} on {appointment_date} at {appointment_time} for a {duration}-minute ({appt_type}) visit. Please tell the user their booking is confirmed and ask if they need anything else."
    except Exception as e:
        return f"An error occurred while booking the appointment for {doctor_name}: {e}"