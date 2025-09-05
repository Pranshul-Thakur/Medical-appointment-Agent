from langchain_core.tools import tool
from src.config import DOCTORS # Import the DOCTORS list from our new config file

@tool
def get_doctor_details() -> str:
    """
    Returns a list of doctors and their specialties. 
    This tool should be used when the user asks for information about the doctors, 
    such as who is available or what their specialties are.
    """
    print("--- Running get_doctor_details tool ---")
    
    if not DOCTORS:
        return "There are currently no doctors listed."
        
    details_list = []
    for doctor in DOCTORS:
        details_list.append(f"- {doctor['name']}, Specialty: {doctor['specialty']}")
        
    return "Of course. Here are the doctors at our clinic:\n" + "\n".join(details_list)