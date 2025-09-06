import sqlite3
import os
import pandas as pd
from datetime import datetime

DB_PATH = os.path.join("data", "clinic.db")
REPORTS_DIR = os.path.join("data", "reports")

def generate_report():
    print("--- Starting Admin Report Generation ---")

    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at '{DB_PATH}'")
        print("Please run 'python -m scripts.setup_database' and book some appointments first.")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)

        query = """
        SELECT
            a.appointment_datetime,
            d.name AS doctor_name,
            p.first_name || ' ' || p.last_name AS patient_name,
            p.patient_id,
            a.duration_minutes
        FROM
            appointments a
        JOIN
            doctors d ON a.doctor_id = d.doctor_id
        JOIN
            patients p ON a.patient_id = p.patient_id
        ORDER BY
            a.appointment_datetime;
        """
    
        report_df = pd.read_sql_query(query, conn)

    except (sqlite3.Error, pd.errors.DatabaseError) as e:
        print(f"Database error: {e}")
        return
    finally:
        if conn:
            conn.close()

    if report_df.empty:
        print("No booked appointments found in the database.")
        return

    report_df['appointment_date'] = pd.to_datetime(report_df['appointment_datetime']).dt.strftime('%Y-%m-%d')
    report_df['appointment_time'] = pd.to_datetime(report_df['appointment_datetime']).dt.strftime('%H:%M')
    report_columns = [
        'appointment_date', 
        'appointment_time', 
        'doctor_name', 
        'patient_name', 
        'patient_id', 
        'duration_minutes'
    ]
    final_report_df = report_df[report_columns]
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)


    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    report_filename = f"appointment_report_{timestamp}.csv"
    report_filepath = os.path.join(REPORTS_DIR, report_filename)
    final_report_df.to_csv(report_filepath, index=False)
    
    print("\n--- Admin Report Generation Successful ---")
    print(f"Found {len(final_report_df)} booked appointments.")
    print(f"Report saved to: {report_filepath}")


if __name__ == "__main__":
    generate_report()