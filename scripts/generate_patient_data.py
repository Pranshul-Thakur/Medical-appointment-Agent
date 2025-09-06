import sqlite3
from faker import Faker
import random
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join("data", "clinic.db")
fake = Faker()
insurance_carriers = [
    "Blue Cross Blue Shield", "UnitedHealthcare", "Aetna", "Cigna",
    "Humana", "Kaiser Permanente", "Anthem", "Centene",
]

def generate_dob():
    today = datetime.today()
    start_date = today - timedelta(days=365 * 80)
    end_date = today - timedelta(days=365 * 18)
    random_date = start_date + (end_date - start_date) * random.random()
    return random_date.strftime("%Y-%m-%d")

def generate_patients(num_patients=50):
    patients = []
    for i in range(1, num_patients + 1):
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1,100)}@example.com"
        
        patient = {
            "patient_id": f"PAT{i:04d}",
            "first_name": first_name,
            "last_name": last_name,
            "dob": generate_dob(),
            "phone_number": fake.phone_number(),
            "email": email,
            "insurance_carrier": random.choice(insurance_carriers),
            "member_id": f"{random.randint(100000000, 999999999)}",
            "group_id": f"GRP{random.randint(1000, 9999)}",
        }
        patients.append(patient)
    return patients

def insert_patients_into_db(patients):
    if not patients:
        print("No patient data to insert.")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("Clearing existing patients from the database...")
        cursor.execute("DELETE FROM patients;")
        
        print(f"Inserting {len(patients)} new synthetic patients into the database...")
        cursor.executemany("""
            INSERT INTO patients (patient_id, first_name, last_name, dob, phone_number, email, insurance_carrier, member_id, group_id)
            VALUES (:patient_id, :first_name, :last_name, :dob, :phone_number, :email, :insurance_carrier, :member_id, :group_id);
        """, patients)
        
        conn.commit()
        print(f"Successfully inserted {len(patients)} patient records into the database.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}.")
        print("Please run 'python -m scripts.setup_database' first to create the database.")
    else:
        patient_data = generate_patients(50)
        insert_patients_into_db(patient_data)