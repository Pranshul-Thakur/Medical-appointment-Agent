import os
import pandas as pd
from datetime import datetime

# Define the source and destination directories
SCHEDULES_DIR = os.path.join("data", "doctor_schedules")
REPORTS_DIR = os.path.join("data", "reports")

def generate_report():
    """
    Scans all doctor schedule Excel files, finds all booked appointments,
    and consolidates them into a single timestamped CSV report.
    """
    print("--- Starting Admin Report Generation ---")

    # Ensure the source directory exists
    if not os.path.exists(SCHEDULES_DIR):
        print(f"Error: Schedules directory not found at '{SCHEDULES_DIR}'")
        return

    all_booked_appointments = []

    # Loop through all files in the schedules directory
    for filename in os.listdir(SCHEDULES_DIR):
        if filename.endswith(".xlsx"):
            file_path = os.path.join(SCHEDULES_DIR, filename)
            
            # Extract doctor name from the filename for the report
            # e.g., 'dr_evelyn_reed_schedule.xlsx' -> 'Dr Evelyn Reed'
            doctor_name = filename.replace("_schedule.xlsx", "").replace("_", " ").title()
            
            try:
                # Read the schedule, ensuring date is treated as a string
                schedule_df = pd.read_excel(file_path, dtype={'Date': str, 'PatientID': str})
                
                # Filter for booked appointments
                booked_df = schedule_df[schedule_df['Status'].str.lower() == 'booked'].copy()
                
                # If there are booked appointments, add the doctor's name and append
                if not booked_df.empty:
                    booked_df['DoctorName'] = doctor_name
                    all_booked_appointments.append(booked_df)
            except Exception as e:
                print(f"Warning: Could not process file {filename}. Error: {e}")

    # Check if any booked appointments were found
    if not all_booked_appointments:
        print("No booked appointments found across all schedules.")
        return

    # Combine all found appointments into a single DataFrame
    report_df = pd.concat(all_booked_appointments, ignore_index=True)

    # Select and reorder columns for the final report
    report_columns = ['Date', 'StartTime', 'DoctorName', 'PatientID', 'AppointmentType']
    final_report_df = report_df[report_columns]

    # Sort the report for readability
    final_report_df = final_report_df.sort_values(by=['Date', 'StartTime'])

    # Ensure the reports directory exists
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

    # Create a timestamped filename for the report
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    report_filename = f"appointment_report_{timestamp}.csv"
    report_filepath = os.path.join(REPORTS_DIR, report_filename)

    # Save the final report to a CSV file
    final_report_df.to_csv(report_filepath, index=False)
    
    print("\n--- Admin Report Generation Successful ---")
    print(f"Found {len(final_report_df)} booked appointments.")
    print(f"Report saved to: {report_filepath}")


if __name__ == "__main__":
    # To run this script, navigate to the root 'ai_medical_scheduler' directory
    # and run the command: python -m scripts.generate_admin_report
    generate_report()
