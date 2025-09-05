import os
import pandas as pd
from datetime import datetime

# Define the source and destination directories
SCHEDULES_DIR = os.path.join("data", "doctor_schedules")
REPORTS_DIR = os.path.join("data", "reports")

def generate_report():
    """
    Scans all doctor schedule Excel files, finds all booked appointments,
    consolidates them into a single, intelligent report with appointment durations,
    and saves it as a timestamped CSV.
    """
    print("--- Starting Smart Admin Report Generation ---")

    if not os.path.exists(SCHEDULES_DIR):
        print(f"Error: Schedules directory not found at '{SCHEDULES_DIR}'")
        return

    all_booked_appointments = []

    # Loop through all schedule files to gather booked slots
    for filename in os.listdir(SCHEDULES_DIR):
        if filename.endswith(".xlsx"):
            file_path = os.path.join(SCHEDULES_DIR, filename)
            doctor_name = filename.replace("_schedule.xlsx", "").replace("_", " ").title()
            
            try:
                schedule_df = pd.read_excel(file_path, dtype={'Date': str, 'PatientID': str})
                booked_df = schedule_df[schedule_df['Status'].str.lower() == 'booked'].copy()
                
                if not booked_df.empty:
                    booked_df['DoctorName'] = doctor_name
                    all_booked_appointments.append(booked_df)
            except Exception as e:
                print(f"Warning: Could not process file {filename}. Error: {e}")

    if not all_booked_appointments:
        print("No booked appointments found across all schedules.")
        return

    # Combine all booked slots into one DataFrame
    combined_df = pd.concat(all_booked_appointments, ignore_index=True)

    # --- NEW INTELLIGENT GROUPING LOGIC ---
    # Sort by patient, date, and time to ensure consecutive slots are together
    combined_df = combined_df.sort_values(by=['PatientID', 'Date', 'StartTime'])

    processed_appointments = []
    processed_indices = set()

    for index, row in combined_df.iterrows():
        if index in processed_indices:
            continue

        patient_id = row['PatientID']
        date = row['Date']
        start_time = row['StartTime']
        
        # Find all consecutive slots for this patient on this day starting from this time
        consecutive_slots = [row]
        processed_indices.add(index)
        
        next_index = index + 1
        while next_index < len(combined_df):
            next_row = combined_df.loc[next_index]
            # Check if the next slot belongs to the same patient on the same day
            if next_row['PatientID'] == patient_id and next_row['Date'] == date:
                 # Check if it's the very next 30-min slot
                last_end_time = pd.to_datetime(consecutive_slots[-1]['EndTime'])
                next_start_time = pd.to_datetime(next_row['StartTime'])
                if last_end_time == next_start_time:
                    consecutive_slots.append(next_row)
                    processed_indices.add(next_index)
                    next_index += 1
                else:
                    break # Not a consecutive slot
            else:
                break # Different patient or day
        
        # Calculate duration and consolidate the appointment
        num_slots = len(consecutive_slots)
        duration_minutes = num_slots * 30
        
        processed_appointments.append({
            'Date': date,
            'StartTime': start_time,
            'DoctorName': row['DoctorName'],
            'PatientID': patient_id,
            'AppointmentType': row['AppointmentType'],
            'Duration (min)': duration_minutes
        })
    
    if not processed_appointments:
        print("No valid appointments to report after processing.")
        return
        
    final_report_df = pd.DataFrame(processed_appointments)

    # Ensure the reports directory exists
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

    # Create a timestamped filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    report_filename = f"appointment_report_{timestamp}.csv"
    report_filepath = os.path.join(REPORTS_DIR, report_filename)

    # Save the final report
    final_report_df.to_csv(report_filepath, index=False)
    
    print("\n--- Smart Admin Report Generation Successful ---")
    print(f"Consolidated {len(final_report_df)} appointments.")
    print(f"Report saved to: {report_filepath}")


if __name__ == "__main__":
    generate_report()