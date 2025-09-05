import pandas as pd
from datetime import datetime, timedelta, time
import os

# --- Configuration ---
# The DOCTORS list is kept here for now to keep changes minimal.
DOCTORS = [
    {"name": "Dr. Evelyn Reed", "specialty": "Allergy & Immunology"},
    {"name": "Dr. Ben Carter", "specialty": "Allergy & Immunology"},
    {"name": "Dr. Olivia Chen", "specialty": "Pediatric Allergy"},
]

WORKING_HOURS = {"start": time(9, 0), "end": time(17, 0)}
LUNCH_BREAK = {"start": time(12, 0), "end": time(13, 0)}
APPOINTMENT_DURATION = timedelta(minutes=30)
SCHEDULE_DAYS = 5 # Generate schedule for the next 5 business days

OUTPUT_DIR = os.path.join("data", "doctor_schedules")

# --- Helper Functions ---

def get_next_business_days(n):
    """Generates the next n business days (Mon-Fri) starting from tomorrow."""
    business_days = []
    current_date = datetime.now().date() + timedelta(days=1)
    while len(business_days) < n:
        if current_date.weekday() < 5: # Monday is 0 and Sunday is 6
            business_days.append(current_date)
        current_date += timedelta(days=1)
    return business_days

# --- Main Script ---

def generate_schedules():
    """Generates and saves a weekly schedule for each doctor."""
    
    # Create the output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created directory: {OUTPUT_DIR}")

    schedule_dates = get_next_business_days(SCHEDULE_DAYS)

    for doctor in DOCTORS:
        doctor_name_slug = doctor["name"].replace(" ", "_").replace(".", "").lower()
        file_path = os.path.join(OUTPUT_DIR, f"{doctor_name_slug}_schedule.xlsx")
        
        all_slots = []

        for day in schedule_dates:
            current_time = datetime.combine(day, WORKING_HOURS["start"])
            end_of_day = datetime.combine(day, WORKING_HOURS["end"])

            while current_time < end_of_day:
                slot_end_time = current_time + APPOINTMENT_DURATION
                
                is_in_lunch = not (current_time.time() >= LUNCH_BREAK["end"] or \
                                   slot_end_time.time() <= LUNCH_BREAK["start"])

                if not is_in_lunch:
                    all_slots.append({
                        "Date": day.strftime("%Y-%m-%d"),
                        "StartTime": current_time.strftime("%H:%M"),
                        "EndTime": slot_end_time.strftime("%H:%M"),
                        "Status": "Available",
                        "PatientID": "",
                        "AppointmentType": ""
                    })
                
                current_time = slot_end_time
        
        # Create a DataFrame and save to Excel
        df = pd.DataFrame(all_slots)
        
        # --- FIX for Pandas FutureWarning ---
        # This is the new line. It explicitly sets the dtype for columns that will hold strings.
        df = df.astype({"PatientID": object, "AppointmentType": object})
        
        df.to_excel(file_path, index=False)
        print(f"Generated schedule for {doctor['name']} at {file_path}")

if __name__ == "__main__":
    # To run this script, navigate to the root 'ai_medical_scheduler' directory
    # and run: python -m scripts.generate_doctor_schedules
    generate_schedules()