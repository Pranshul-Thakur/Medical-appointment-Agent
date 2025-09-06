import sqlite3
import os
from langchain_core.tools import tool

DB_PATH = os.path.join("data", "clinic.db")

def db_connect():
    """Establishes a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)

@tool
def get_doctor_details() -> str:
    """
    Retrieves a list of all available doctors and their specialties from the database.
    This tool is used when the patient wants to know which doctors are available.
    """
    print("--- Running get_doctor_details tool (DB Version) ---")
    conn = db_connect()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT name, specialty FROM doctors ORDER BY name;")
        doctors = cursor.fetchall()
        conn.close()

        if not doctors:
            return "There are currently no doctors available."

        details_str = "Of course. Here is a list of our available doctors and their specialties:\n"
        for doctor in doctors:
            details_str += f"- {doctor[0]}, Specialty: {doctor[1]}\n"
        
        return details_str.strip()

    except sqlite3.Error as e:
        if conn:
            conn.close()
        return f"Database error while fetching doctors: {e}"