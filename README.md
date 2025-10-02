# Medical Appointment Scheduling AI Agent

An intelligent conversational agent built with LangGraph and Google's Gemini AI that automates medical appointment scheduling for allergy and wellness clinics. The system handles patient lookup, appointment booking, and automated email confirmations with integrated intake forms.

## Features

- **Intelligent Patient Management**: Automatically identifies returning patients and creates new patient records
- **Multi-Doctor Scheduling**: Supports multiple doctors with different specialties
- **Interactive Calendar Interface**: Visual appointment slot selection through Streamlit
- **Automated Email System**: Generates personalized confirmation emails with intake forms using Gmail API
- **Smart Reminder System**: Sends automated appointment reminders at 7, 3, and 1-day intervals
- **Database-Driven**: SQLite database for persistent storage of patients, doctors, and appointments
- **AI-Powered Communication**: Uses Gemini 1.5 Flash for natural language processing and email drafting

## Architecture

The system uses a state graph architecture with LangGraph, implementing a strict workflow:

1. Patient information gathering and lookup
2. New patient record completion (if necessary)
3. Doctor selection and availability checking
4. Appointment confirmation and booking
5. Automated confirmation email with intake form

## Tech Stack

- **AI Framework**: LangGraph, LangChain
- **LLM**: Google Gemini 1.5 Flash
- **Frontend**: Streamlit with streamlit-calendar
- **Database**: SQLite3
- **Email Integration**: Gmail API with OAuth2
- **Data Processing**: Pandas, Faker (for synthetic data)

## Project Structure

```
├── src/
│   ├── agent.py                 # Main agent logic and state graph
│   ├── main.py                  # Streamlit UI application
│   ├── config.py                # Doctor configurations
│   └── tools/
│       ├── patient_tools.py     # Patient lookup and record management
│       ├── schedule_tools.py    # Availability checking and booking
│       ├── clinic_tools.py      # Doctor information retrieval
│       └── communication_tools.py # Email drafting and sending
├── scripts/
│   ├── generate_doctor_schedules.py  # Database setup and availability generation
│   ├── generate_patient_data.py      # Synthetic patient data creation
│   ├── generate_admin_report.py      # Appointment reporting
│   └── send_reminders.py             # Automated reminder system
└── data/
    ├── clinic.db                # SQLite database
    └── reports/                 # Generated CSV reports
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Pranshul-Thakur/medical-appointment-agent.git
cd medical-appointment-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with your Google API key:
```
GOOGLE_API_KEY=your_api_key_here
```

4. Set up Gmail API credentials:
- Create a project in Google Cloud Console
- Enable Gmail API
- Download `credentials.json` and place it in the root directory

## Usage

### Initialize Database

Set up the database with doctor schedules:
```bash
python -m scripts.generate_doctor_schedules
```

Generate synthetic patient data:
```bash
python -m scripts.generate_patient_data
```

### Run the Application

Start the Streamlit interface:
```bash
streamlit run src/main.py
```

### Generate Reports

Create an admin report of all appointments:
```bash
python -m scripts.generate_admin_report
```

### Send Reminders

Run the automated reminder system:
```bash
python -m scripts.send_reminders
```

## Database Schema

**Patients Table**: Stores patient demographics and insurance information

**Doctors Table**: Contains doctor names and specialties

**Appointments Table**: Records all booked appointments with status

**Availability Table**: Manages doctor schedules and slot bookings

## Configuration

Edit `src/config.py` to modify doctor listings:
```python
DOCTORS = [
    {"name": "Dr. Evelyn Reed", "specialty": "Allergy & Immunology"},
    {"name": "Dr. Ben Carter", "specialty": "Allergy & Immunology"},
    {"name": "Dr. Olivia Chen", "specialty": "Pediatric Allergy"},
]
```

## Agent Workflow

The agent follows a strict conversational flow:

1. Greets user and requests patient information (name and DOB)
2. Looks up patient in database or creates new record
3. Collects additional information for new patients
4. Presents available doctors and their specialties
5. Checks appointment availability based on date preference
6. Confirms appointment details with user
7. Books appointment and updates database
8. Generates and drafts confirmation email with intake form

## Email Features

The system automatically generates professional emails for:

- Appointment confirmations with intake form links
- 7-day advance reminders
- 3-day urgent reminders with confirmation requests
- 1-day final reminders

All emails are drafted in Gmail for review before sending.

## Security Notes

- Store `credentials.json` and `token.json` securely
- Keep `.env` file private (already in `.gitignore`)
- Database credentials should be managed separately in production
- OAuth tokens are stored locally in `token.json`

## Requirements

- Python 3.8+
- Google API credentials
- Gmail account for email features
- Sufficient API quota for Gemini

## Contributing

Contributions are welcome. Please ensure all tools follow the established pattern and maintain the strict workflow logic.

## License

This project is provided as-is for educational and demonstration purposes.
