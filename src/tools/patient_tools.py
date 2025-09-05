import pandas as pd
import os
from langchain_core.tools import tool

# Define the path to the patient data
PATIENT_DATA_PATH = os.path.join('data', 'patients.csv')

@tool
def lookup_patient(full_name: str, dob: str) -> str:
    """
    Looks up a patient by their full name and date of birth. Returns the patient's status and their PatientID.

    Args:
        full_name: The patient's full name (e.g., "John Doe").
        dob: The patient's date of birth in YYYY-MM-DD format.

    Returns:
        A string confirming the patient's status (new or returning), their PatientID, and if they are missing contact info.
    """
    print(f"--- Running Patient Lookup for {full_name}, DOB: {dob} ---")
    
    if not os.path.exists(PATIENT_DATA_PATH):
        return "Error: Patient data file not found."
    
    patients_df = pd.read_csv(PATIENT_DATA_PATH)
    
    try:
        first_name, last_name = full_name.strip().split(maxsplit=1)
    except ValueError:
        return "Invalid name format. Please provide both a first and last name."

    match = patients_df[
        (patients_df['FirstName'].str.lower() == first_name.lower()) &
        (patients_df['LastName'].str.lower() == last_name.lower()) &
        (patients_df['DateOfBirth'] == dob)
    ]

    if not match.empty:
        patient_id = match.iloc[0]['PatientID']
        return f"Patient found. Record for {full_name}, PatientID: {patient_id}. This is a returning patient."
    else:
        new_patient_id = f"PAT{len(patients_df) + 1:04d}"
        new_patient = pd.DataFrame([{
            "PatientID": new_patient_id, "FirstName": first_name, "LastName": last_name, "DateOfBirth": dob,
            "Email": None, "PhoneNumber": None # Explicitly set contact info as missing
        }])
        patients_df = pd.concat([patients_df, new_patient], ignore_index=True)
        patients_df.to_csv(PATIENT_DATA_PATH, index=False)
        print(f"New patient created. Total patients: {len(patients_df)}")
        return f"Patient record for {full_name} not found. A new record has been created with PatientID: {new_patient_id}. This is a new patient. CRITICAL: You must now ask the user for their email and phone number and use the update_patient_record tool."

@tool
def update_patient_record(patient_id: str, email: str = None, phone_number: str = None) -> str:
    """
    Updates a patient's record with their email and/or phone number.

    Args:
        patient_id: The unique ID of the patient to update.
        email: The patient's email address.
        phone_number: The patient's phone number.

    Returns:
        A string confirming that the record has been updated.
    """
    print(f"--- Running Update Patient Record for {patient_id} ---")
    if not os.path.exists(PATIENT_DATA_PATH):
        return "Error: Patient data file not found."

    patients_df = pd.read_csv(PATIENT_DATA_PATH)
    patient_index = patients_df[patients_df['PatientID'] == patient_id].index

    if patient_index.empty:
        return f"Error: Patient with ID {patient_id} not found."

    if email:
        patients_df.loc[patient_index, 'Email'] = email
    if phone_number:
        patients_df.loc[patient_index, 'PhoneNumber'] = phone_number

    patients_df.to_csv(PATIENT_DATA_PATH, index=False)
    return f"Patient record for {patient_id} has been successfully updated with the new contact information."