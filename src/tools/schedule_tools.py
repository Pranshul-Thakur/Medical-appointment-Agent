import pandas as pd
import os
from langchain_core.tools import tool

# --- Helper function to load schedule data ---
def load_schedule_data(file_path):
    """
    Loads a doctor's schedule from an Excel file, ensuring Date is a string.
    """
    try:
        # --- THE FIX: Explicitly define the data types for each column ---
        # This prevents pandas from auto-converting dates to a different format.
        dtype_spec = {
            'Date': str,
            'StartTime': str,
            'EndTime': str,
            'Status': str,
            'PatientID': str,
            'AppointmentType': str
        }
        return pd.read_excel(file_path, dtype=dtype_spec)
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error loading schedule file {file_path}: {e}")
        return None

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

    schedule_df = load_schedule_data(file_path)

    if schedule_df is None:
        return f"Schedule for {doctor_name} not found. Please check the name. Available doctors are Dr. Evelyn Reed, Dr. Ben Carter, and Dr. Olivia Chen."

    available_slots = schedule_df[schedule_df['Status'].str.lower() == 'available']

    if available_slots.empty:
        return f"No available appointments found for {doctor_name}."

    # --- NEW, CLEANER FORMATTING ---
    availability_str = f"Of course. Here are the available slots for {doctor_name}:\n"
    # Group by date and list the available times in a structured way
    for date, group in available_slots.groupby('Date'):
        # Convert date string to a more readable format if possible
        try:
            readable_date = pd.to_datetime(date).strftime('%A, %B %d, %Y')
            availability_str += f"\n--- {readable_date} ---\n"
        except:
            availability_str += f"\n--- {date} ---\n"
        
        morning_slots = [time for time in group['StartTime'] if int(time.split(':')[0]) < 12]
        afternoon_slots = [time for time in group['StartTime'] if int(time.split(':')[0]) >= 12]

        if morning_slots:
            availability_str += "Morning:   " + ", ".join(morning_slots) + "\n"
        if afternoon_slots:
            availability_str += "Afternoon: " + ", ".join(afternoon_slots) + "\n"
    
    return availability_str.strip()

@tool
def book_appointment(doctor_name: str, appointment_date: str, appointment_time: str, patient_id: str, patient_status: str) -> str:
    """
    Books an appointment for a patient with a specific doctor at a given date and time.

    Args:
        doctor_name: The full name of the doctor (e.g., "Dr. Evelyn Reed").
        appointment_date: The date of the appointment in YYYY-MM-DD format.
        appointment_time: The start time of the appointment in HH:MM format.
        patient_id: The unique ID of the patient (e.g., "PAT0051").
        patient_status: The patient's status, either "new patient" or "returning patient".

    Returns:
        A string confirming the booking or providing an error message.
    """
    print(f"--- Running Appointment Booking for {patient_id} with {doctor_name} ---")
    doctor_name_slug = doctor_name.replace(" ", "_").replace(".", "").lower()
    file_path = os.path.join("data", "doctor_schedules", f"{doctor_name_slug}_schedule.xlsx")

    schedule_df = load_schedule_data(file_path)
    if schedule_df is None:
        return f"Schedule for {doctor_name} not found. Cannot book appointment."

    duration = 60 if "new" in patient_status.lower() else 30
    appt_type = "New Patient" if duration == 60 else "Returning Patient"
    num_slots_to_book = 2 if duration == 60 else 1

    # --- MORE ROBUST FIX FOR THE BOOKING BUG ---
    # Ensure both sides of the comparison are clean strings
    target_indices = schedule_df[
        (schedule_df['Date'].str.strip() == appointment_date.strip()) &
        (schedule_df['StartTime'].str.strip() == appointment_time.strip())
    ].index

    if target_indices.empty:
        return f"The requested time slot ({appointment_time} on {appointment_date}) is not available or does not exist."

    start_index = target_indices[0]
    
    # Check if consecutive slots are available
    slots_to_update = []
    for i in range(num_slots_to_book):
        current_index = start_index + i
        if current_index >= len(schedule_df) or schedule_df.loc[current_index, 'Status'].lower() != 'available':
            return f"Cannot book a {duration}-minute appointment at {appointment_time}. Not enough consecutive slots are available."
        slots_to_update.append(current_index)

    # Book the slots
    for index in slots_to_update:
        schedule_df.loc[index, 'Status'] = 'Booked'
        schedule_df.loc[index, 'PatientID'] = patient_id
        schedule_df.loc[index, 'AppointmentType'] = appt_type

    schedule_df.to_excel(file_path, index=False)
    
    return f"Appointment successfully booked for PatientID {patient_id} with {doctor_name} on {appointment_date} at {appointment_time} for a {duration}-minute ({appt_type}) session."