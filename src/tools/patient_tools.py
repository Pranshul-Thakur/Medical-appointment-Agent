import sqlite3
import os
from langchain_core.tools import tool
from typing import Optional

DB_PATH = os.path.join("data", "clinic.db")

def db_connect():
    """Establishes a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)

@tool
def lookup_patient(full_name: str, dob: Optional[str] = None) -> str:
    """
    Looks up a patient by full name. If a record is found, it confirms them as a returning patient.
    If no record is found, it requires a DOB to create a new patient.
    This tool provides explicit instructions for the agent's next action.

    Args:
        full_name: The patient's full name (e.g., "John Doe").
        dob: The patient's date of birth in YYYY-MM-DD format (optional).
    """
    print(f"--- Running Patient Lookup for {full_name} ---")
    conn = db_connect()
    cursor = conn.cursor()

    try:
        first_name, last_name = full_name.strip().split(maxsplit=1)
    except ValueError:
        conn.close()
        return "Invalid name format. Please provide both a first and last name."

    # First, try to find a patient by name
    cursor.execute(
        "SELECT patient_id FROM patients WHERE lower(first_name) = ? AND lower(last_name) = ?",
        (first_name.lower(), last_name.lower())
    )
    patient = cursor.fetchone()

    if patient:
        # If a patient is found by name, we consider them returning as per the new logic.
        patient_id = patient[0]
        conn.close()
        return f"Patient found. Record for {full_name}, PatientID: {patient_id}. This is a returning patient. You can now proceed to booking."
    else:
        # If no patient is found by name, we check if a DOB was provided to create one
        if dob:
            new_patient_id = f"PAT{cursor.execute('SELECT COUNT(*) FROM patients').fetchone()[0] + 1:04d}"
            cursor.execute(
                "INSERT INTO patients (patient_id, first_name, last_name, dob) VALUES (?, ?, ?, ?)",
                (new_patient_id, first_name, last_name, dob)
            )
            conn.commit()
            conn.close()
            print(f"New patient created with ID: {new_patient_id}")
            return f"A new patient record was created with PatientID: {new_patient_id}. You MUST now ask for their email, phone number, and insurance details to complete the record."
        else:
            # If no patient is found and no DOB is provided, instruct the agent to get the DOB.
            conn.close()
            return "No patient found with that name. You MUST now ask for their Date of Birth (YYYY-MM-DD) to create a new patient record."

@tool
def update_patient_record(patient_id: str, email: str = None, phone_number: str = None, insurance_carrier: str = None, member_id: str = None, group_id: str = None) -> str:
    """
    Updates a patient's record with their contact and/or insurance details.

    Args:
        patient_id: The unique ID of the patient.
        email: The patient's email address.
        phone_number: The patient's phone number.
        insurance_carrier: The name of the insurance company.
        member_id: The patient's insurance member ID.
        group_id: The patient's insurance group ID.
    """
    print(f"--- Running Update Patient Record for {patient_id} ---")
    conn = db_connect()
    cursor = conn.cursor()

    try:
        # Build the update query dynamically based on provided arguments
        updates = []
        params = []
        if email:
            updates.append("email = ?")
            params.append(email)
        if phone_number:
            updates.append("phone_number = ?")
            params.append(phone_number)
        if insurance_carrier:
            updates.append("insurance_carrier = ?")
            params.append(insurance_carrier)
        if member_id:
            updates.append("member_id = ?")
            params.append(member_id)
        if group_id:
            updates.append("group_id = ?")
            params.append(group_id)

        if not updates:
            return "No information provided to update."

        params.append(patient_id)
        query = f"UPDATE patients SET {', '.join(updates)} WHERE patient_id = ?"
        
        cursor.execute(query, tuple(params))
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            return f"Error: Patient with ID {patient_id} not found."
            
        conn.close()
        return f"Successfully updated record for PatientID {patient_id}."

    except sqlite3.Error as e:
        if conn:
            conn.close()
        return f"Database error while updating patient record: {e}"