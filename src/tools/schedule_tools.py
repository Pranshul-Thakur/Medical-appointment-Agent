import sqlite3
import os
from langchain_core.tools import tool
from typing import Optional
from dateutil.parser import parse, ParserError
from datetime import datetime, timedelta

DB_PATH = os.path.join("data", "clinic.db")

def db_connect():
    """Establishes a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)

def find_doctor_id_by_name(conn, name_query: str) -> Optional[str]:
    """
    Finds a doctor's ID using a forgiving search logic.
    """
    cursor = conn.cursor()
    # Clean the input query
    clean_query = name_query.lower().replace("dr.", "").strip()
    
    # 1. Try a LIKE search on the full name - this is the most common case
    cursor.execute("SELECT doctor_id FROM doctors WHERE lower(name) LIKE ?", (f'%{clean_query}%',))
    result = cursor.fetchone()
    if result:
        return result[0]
        
    # 2. If that fails, split the query and search for any word in the name
    words = clean_query.split()
    if not words:
        return None
    
    like_clauses = " OR ".join(["lower(name) LIKE ?"] * len(words))
    params = [f'%{word}%' for word in words]
    
    cursor.execute(f"SELECT doctor_id FROM doctors WHERE {like_clauses}", params)
    result = cursor.fetchone()
    if result:
        return result[0]
        
    return None # Return None if no doctor is found

@tool
def check_availability(doctor_name: str, date: Optional[str] = None) -> str:
    """
    Checks the schedule for a specific doctor to find available appointment slots.
    """
    print(f"--- Running Availability Check for {doctor_name} ---")
    conn = db_connect()
    
    try:
        doctor_id = find_doctor_id_by_name(conn, doctor_name)
        if not doctor_id:
            return f"Doctor '{doctor_name}' not found. Use `get_doctor_details` for a list of doctors."

        cursor = conn.cursor()
        query = ""
        params = [doctor_id]

        if date and date.strip():
            try:
                parsed_date = parse(date)
                query_date_str = parsed_date.strftime("%Y-%m-%d")
                query = "SELECT start_time FROM availability WHERE doctor_id = ? AND date(start_time) = ? AND is_booked = 0 ORDER BY start_time;"
                params.append(query_date_str)
            except (ValueError, ParserError):
                return "Invalid date format. Please provide a clear date like 'September 8th, 2025'."
        else:
            query = "SELECT start_time FROM availability WHERE doctor_id = ? AND is_booked = 0 ORDER BY start_time;"

        cursor.execute(query, tuple(params))
        slots = cursor.fetchall()

        if not slots:
            return f"No available appointments found for {doctor_name}."

        slots_by_date = {}
        for slot in slots:
            dt = datetime.strptime(slot[0], "%Y-%m-%d %H:%M")
            d = dt.strftime("%Y-%m-%d")
            t = dt.strftime("%H:%M")
            if d not in slots_by_date: slots_by_date[d] = []
            slots_by_date[d].append(t)

        availability_str = f"Of course. Here are the available slots for {doctor_name}:\n"
        for d, times in sorted(slots_by_date.items()):
            readable_date = datetime.strptime(d, "%Y-%m-%d").strftime('%A, %B %d, %Y')
            availability_str += f"\n--- {readable_date} ---\n"
            morning_slots = [t for t in times if int(t.split(':')[0]) < 12]
            afternoon_slots = [t for t in times if int(t.split(':')[0]) >= 12]
            if morning_slots: availability_str += "Morning:   " + ", ".join(morning_slots) + "\n"
            if afternoon_slots: availability_str += "Afternoon: " + ", ".join(afternoon_slots) + "\n"

        return availability_str.strip()

    finally:
        if conn:
            conn.close()

@tool
def book_appointment(doctor_name: str, appointment_date: str, appointment_time: str, patient_id: str, patient_status: str) -> str:
    """
    Books an appointment for a patient.
    """
    print(f"--- Running Appointment Booking for {patient_id} with {doctor_name} ---")
    
    try:
        parsed_datetime = parse(f"{appointment_date} {appointment_time}")
        if parsed_datetime < datetime.now():
            parsed_datetime = parsed_datetime.replace(year=datetime.now().year + 1)
        appointment_datetime_str = parsed_datetime.strftime("%Y-%m-%d %H:%M")
    except (ValueError, ParserError):
        return "Invalid date or time format provided."

    conn = db_connect()
    try:
        doctor_id = find_doctor_id_by_name(conn, doctor_name)
        if not doctor_id:
            return f"Doctor '{doctor_name}' not found."
        
        cursor = conn.cursor()
        duration = 60 if "new" in patient_status.lower() else 30
        
        cursor.execute("SELECT slot_id FROM availability WHERE doctor_id = ? AND start_time = ? AND is_booked = 0", (doctor_id, appointment_datetime_str))
        slot = cursor.fetchone()

        if not slot:
            return f"The requested time slot ({appointment_datetime_str}) is not available."
        
        slot_id_to_book = slot[0]
        cursor.execute("UPDATE availability SET is_booked = 1 WHERE slot_id = ?", (slot_id_to_book,))
        
        if duration == 60:
            next_slot_time = (parsed_datetime + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M")
            cursor.execute("SELECT slot_id FROM availability WHERE doctor_id = ? AND start_time = ? AND is_booked = 0", (doctor_id, next_slot_time))
            next_slot = cursor.fetchone()
            if not next_slot:
                conn.rollback()
                return f"Cannot book a 60-minute appointment. The consecutive slot at {next_slot_time} is not available."
            cursor.execute("UPDATE availability SET is_booked = 1 WHERE slot_id = ?", (next_slot[0],))

        cursor.execute("INSERT INTO appointments (doctor_id, patient_id, appointment_datetime, duration_minutes) VALUES (?, ?, ?, ?)", (doctor_id, patient_id, appointment_datetime_str, duration))
        
        conn.commit()
        return (f"Appointment successfully booked for PatientID {patient_id}. "
                f"CRITICAL: Your next and final action MUST be to call the `send_confirmation_with_form` tool to complete the process.")

    except sqlite3.Error as e:
        if conn: conn.rollback()
        return f"Database error while booking appointment: {e}"
    finally:
        if conn: conn.close()