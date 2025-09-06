import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join("data", "clinic.db")
DATA_DIR = "data"

DOCTORS = [
    {"id": "DOC001", "name": "Dr. Evelyn Reed", "specialty": "Allergy & Immunology"},
    {"id": "DOC002", "name": "Dr. Ben Carter", "specialty": "Allergy & Immunology"},
    {"id": "DOC003", "name": "Dr. Olivia Chen", "specialty": "Pediatric Allergy"},
]

def create_connection():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        print(f"--- SQLite connection to {DB_PATH} successful ---")
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
    return conn

def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(f"Error creating table: {e}")

def setup_database():
    sql_create_patients_table = """
    CREATE TABLE IF NOT EXISTS patients (
        patient_id TEXT PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        dob TEXT NOT NULL,
        phone_number TEXT,
        email TEXT,
        insurance_carrier TEXT,
        member_id TEXT,
        group_id TEXT
    );
    """

    sql_create_doctors_table = """
    CREATE TABLE IF NOT EXISTS doctors (
        doctor_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        specialty TEXT NOT NULL
    );
    """

    sql_create_appointments_table = """
    CREATE TABLE IF NOT EXISTS appointments (
        appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id TEXT NOT NULL,
        patient_id TEXT NOT NULL,
        appointment_datetime TEXT NOT NULL,
        duration_minutes INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'Booked',
        FOREIGN KEY (doctor_id) REFERENCES doctors (doctor_id),
        FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
    );
    """
    
    sql_create_availability_table = """
    CREATE TABLE IF NOT EXISTS availability (
        slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        is_booked INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (doctor_id) REFERENCES doctors (doctor_id)
    );
    """

    conn = create_connection()

    if conn is not None:
        print("Creating tables...")
        create_table(conn, sql_create_patients_table)
        create_table(conn, sql_create_doctors_table)
        create_table(conn, sql_create_appointments_table)
        create_table(conn, sql_create_availability_table)
        
        print("Populating doctors table...")
        cursor = conn.cursor()
        try:
            cursor.executemany("INSERT OR IGNORE INTO doctors (doctor_id, name, specialty) VALUES (:id, :name, :specialty);", DOCTORS)
            conn.commit()
            print(f"Successfully added/updated {len(DOCTORS)} doctors.")
        except sqlite3.Error as e:
            print(f"Error inserting doctors: {e}")
            
        print("Generating doctor availability for the next 7 days...")
        populate_availability(conn)

        conn.close()
        print("--- Database setup complete. ---")
    else:
        print("Error! Cannot create the database connection.")

def populate_availability(conn):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM availability;")
    
    today = datetime.now()
    availability_slots = []
    
    for day in range(7):
        current_date = today + timedelta(days=day)
        if current_date.weekday() >= 5:
            continue
            
        date_str = current_date.strftime("%Y-%m-%d")

        for doctor in DOCTORS:
            for hour in range(9, 12):
                for minute in [0, 30]:
                    start_time = f"{date_str} {hour:02d}:{minute:02d}"
                    availability_slots.append((doctor['id'], start_time, (datetime.strptime(start_time, "%Y-%m-%d %H:%M") + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M")))

            for hour in range(13, 17):
                 for minute in [0, 30]:
                    start_time = f"{date_str} {hour:02d}:{minute:02d}"
                    availability_slots.append((doctor['id'], start_time, (datetime.strptime(start_time, "%Y-%m-%d %H:%M") + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M")))

    try:
        cursor.executemany("INSERT INTO availability (doctor_id, start_time, end_time) VALUES (?, ?, ?);", availability_slots)
        conn.commit()
        print(f"Successfully generated {len(availability_slots)} availability slots.")
    except sqlite3.Error as e:
        print(f"Error inserting availability: {e}")


if __name__ == "__main__":
    setup_database()