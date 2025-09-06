import os
from dotenv import load_dotenv
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import AnyMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import ToolNode

# --- Import All Final Tools ---
from src.tools.patient_tools import lookup_patient, update_patient_record
from src.tools.schedule_tools import check_availability, book_appointment
from src.tools.clinic_tools import get_doctor_details
from src.tools.communication_tools import send_confirmation_with_form

# --- 1. Load Environment Variables ---
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("API key not found. Please set the GOOGLE_API_KEY in your .env file.")

# --- 2. Define Agent State ---
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

# --- 3. Define the Agent's Brain (LLM) and All Tools ---
tools = [
    lookup_patient,
    update_patient_record,
    check_availability,
    book_appointment,
    get_doctor_details,
    send_confirmation_with_form
]
tool_node = ToolNode(tools)

model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=API_KEY, convert_system_message_to_human=True)
model = model.bind_tools(tools)

# --- 4. Define Agent Logic (Nodes for the Graph) ---
def should_continue(state: AgentState) -> str:
    last_message = state['messages'][-1]
    if not last_message.tool_calls:
        return "end"
    return "continue"

def call_model(state: AgentState) -> dict[str, any]:
    messages = state['messages']
    response = model.invoke(messages)
    return {"messages": [response]}

# --- 5. Construct the Agent Graph ---
# --- THE FINAL, ULTRA-STRICT PROMPT ---
SYSTEM_PROMPT = """You are a medical appointment scheduling assistant. Your ONLY job is to help users book appointments by calling tools in a specific, rigid order. Do not deviate or take shortcuts.

**WORKFLOW: FOLLOW THESE STEPS EXACTLY.**

**1. GATHER PATIENT INFO:**
   - Greet the user and ask for their full name and date of birth (DOB).
   - Once you have BOTH pieces of information, call the `lookup_patient` tool with the `full_name` and `dob`.

**2. COMPLETE NEW PATIENT RECORD (if necessary):**
   - **IF** the `lookup_patient` output indicates a new patient was created:
     - You MUST STOP. Your immediate next action is to ask for the patient's email, phone number, and insurance details.
     - After you get this information, call the `update_patient_record` tool.

**3. FIND APPOINTMENT SLOT:**
   - Ask the user which doctor they want to see. You can use `get_doctor_details` if they ask for a list.
   - Then, ask what date they are interested in.
   - Call the `check_availability` tool with the `doctor_name` and `date`.

**4. CONFIRM AND BOOK:**
   - Present the available times from the tool output.
   - When the user chooses a time, you MUST summarize all details for a final confirmation.
   - **Example Summary:** "OK. Just to confirm, you want to book an appointment for [Patient Name] with [Doctor Name] on [Date in YYYY-MM-DD] at [Time in HH:MM]. Is that correct?"
   - **AFTER** the user explicitly says "yes" or "correct" to your summary, call the `book_appointment` tool.
   - Use the exact, formatted date and time from your summary.
   - You MUST use the `patient_id` and `patient_status` from the earlier `lookup_patient` tool output.

**5. SEND CONFIRMATION EMAIL (MANDATORY FINAL STEP):**
   - **IF** the `book_appointment` tool succeeds, its output will be a CRITICAL instruction.
   - Your ONLY next action is to call the `send_confirmation_with_form` tool. You must find all required arguments from the conversation history.

**6. CONCLUDE:**
   - After the `send_confirmation_with_form` tool succeeds, inform the user that a confirmation draft has been created in their Gmail, and then politely say goodbye.
"""

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("action", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"continue": "action", "end": END},
)
workflow.add_edge("action", "agent")

app = workflow.compile()
print("Agent graph compiled successfully.")

app = app.with_config({"initial_state": {"messages": [SystemMessage(content=SYSTEM_PROMPT)]}})