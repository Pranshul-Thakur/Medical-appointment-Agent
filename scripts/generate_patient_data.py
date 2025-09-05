import csv
from faker import Faker
import random
from datetime import datetime, timedelta
import os

# Initialize Faker to generate synthetic data
fake = Faker()

# List of sample insurance carriers
insurance_carriers = [
    "Blue Cross Blue Shield",
    "UnitedHealthcare",
    "Aetna",
    "Cigna",
    "Humana",
    "Kaiser Permanente",
    "Anthem",
    "Centene",
]

def generate_dob():
    """Generates a random date of birth for a person between 18 and 80 years old."""
    today = datetime.today()
    start_date = today - timedelta(days=365 * 80)
    end_date = today - timedelta(days=365 * 18)
    random_date = start_date + (end_date - start_date) * random.random()
    return random_date.strftime("%Y-%m-%d")

def generate_patients(num_patients=50):
    """Generates a list of synthetic patient data."""
    patients = []
    for i in range(1, num_patients + 1):
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1,100)}@example.com"
        
        patient = {
            "PatientID": f"PAT{i:04d}",
            "FirstName": first_name,
            "LastName": last_name,
            "DateOfBirth": generate_dob(),
            "PhoneNumber": fake.phone_number(),
            "Email": email,
            "InsuranceCarrier": random.choice(insurance_carriers),
            "MemberID": f"{random.randint(100000000, 999999999)}",
            "GroupID": f"GRP{random.randint(1000, 9999)}",
        }
        patients.append(patient)
    return patients

def save_to_csv(patients, filename="patients.csv"):
    """Saves the patient data to a CSV file inside the 'data' directory."""
    if not patients:
        print("No patient data to save.")
        return

    # --- THIS IS THE CORRECTED LOGIC ---
    # Define the output directory relative to the project root
    output_dir = "data"
    
    # Create the directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Join the directory and filename to create the full path
    filepath = os.path.join(output_dir, filename)
    # ------------------------------------

    headers = patients[0].keys()
    
    with open(filepath, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(patients)
    print(f"Successfully generated and saved {len(patients)} patient records to {filepath}")


if __name__ == "__main__":
    # To run this script, navigate to the root 'ai_medical_scheduler' directory
    # and run the command: python scripts/generate_patient_data.py
    
    patient_data = generate_patients(50)
    
    # Save the data to a CSV file in the 'data' folder
    save_to_csv(patient_data)