import pandas as pd
import os
from langchain_core.tools import tool
from typing import Optional

# Define the path to the patient data
PATIENT_DATA_PATH = os.path.join('data', 'patients.csv')

# --- Helper function to load data ---
def load_patient_data():
    """Loads the patient data from the CSV file."""
    try:
        return pd.read_csv(PATIENT_DATA_PATH)
    except FileNotFoundError:
        print(f"Error: The file {PATIENT_DATA_PATH} was not found.")
        return None

@tool
def lookup_patient(full_name: str, dob: Optional[str] = None) -> str:
    """
    Looks up a patient by full name and optionally DOB.
    - If only name is provided, it checks for a record.
    - If name and DOB are provided, it verifies the patient or creates a new one.
    This tool provides explicit instructions for the agent's next action.

    Args:
        full_name: The patient's full name (e.g., "John Doe").
        dob: The patient's date of birth in YYYY-MM-DD format (optional).

    Returns:
        A string with the lookup result and a direct command for the agent's next step.
    """
    print(f"--- Running Patient Lookup for {full_name} ---")
    patients_df = load_patient_data()
    if patients_df is None:
        return "Error: Patient data file not found."

    try:
        first_name, last_name = full_name.strip().split(maxsplit=1)
    except ValueError:
        return "Invalid name format. Please provide both a first and last name."

    name_match = patients_df[
        (patients_df['FirstName'].str.lower() == first_name.lower()) &
        (patients_df['LastName'].str.lower() == last_name.lower())
    ]

    if dob:
        dob_match = name_match[name_match['DateOfBirth'] == dob]
        if not dob_match.empty:
            patient_id = dob_match.iloc[0]['PatientID']
            return f"Patient verified. Record for {full_name}, PatientID: {patient_id}. This is a returning patient."
        else:
            new_patient_id = f"PAT{len(patients_df) + 1:04d}"
            new_patient = pd.DataFrame([{
                "PatientID": new_patient_id, "FirstName": first_name, "LastName": last_name, "DateOfBirth": dob,
                "PhoneNumber": None, "Email": None, "InsuranceCarrier": None, "MemberID": None, "GroupID": None
            }])
            patients_df = pd.concat([patients_df, new_patient], ignore_index=True)
            patients_df.to_csv(PATIENT_DATA_PATH, index=False)
            print(f"New patient created. Total patients: {len(patients_df)}")
            
            # --- THE FIX: This is now an explicit command ---
            return f"A new patient record was created with PatientID: {new_patient_id}. CRITICAL: You MUST now ask the user for their email, phone number, and insurance details to complete the record using the `update_patient_record` tool."
    else:
        if not name_match.empty:
            return f"A record with that name was found. To proceed, please ask the user for their date of birth to verify their identity."
        else:
            return f"No patient found with that name. To proceed, please ask the user for their date of birth to create a new patient record."

@tool
def update_patient_record(patient_id: str, email: str = None, phone_number: str = None, insurance_carrier: str = None, member_id: str = None, group_id: str = None) -> str:
    """
    Updates a patient's record with their contact information AND/OR their insurance details.
    This tool should be used to add information for new patients.

    Args:
        patient_id: The unique ID of the patient (e.g., "PAT0051").
        email: The patient's email address.
        phone_number: The patient's phone number.
        insurance_carrier: The name of the insurance company.
        member_id: The patient's insurance member ID.
        group_id: The patient's insurance group ID.

    Returns:
        A string confirming that the patient's record has been updated.
    """
    print(f"--- Running Update Patient Record for {patient_id} ---")
    patients_df = load_patient_data()
    if patients_df is None:
        return "Error: Patient data file not found."

    if patient_id not in patients_df['PatientID'].values:
        return f"Error: Patient with ID {patient_id} not found."

    patient_index = patients_df[patients_df['PatientID'] == patient_id].index[0]

    if email:
        patients_df.loc[patient_index, 'Email'] = email
    if phone_number:
        patients_df.loc[patient_index, 'PhoneNumber'] = phone_number
    if insurance_carrier:
        patients_df.loc[patient_index, 'InsuranceCarrier'] = insurance_carrier
    if member_id:
        patients_df.loc[patient_index, 'MemberID'] = member_id
    if group_id:
        patients_df.loc[patient_index, 'GroupID'] = group_id
    
    patients_df.to_csv(PATIENT_DATA_PATH, index=False)
    
    return f"Successfully updated record for PatientID {patient_id}."