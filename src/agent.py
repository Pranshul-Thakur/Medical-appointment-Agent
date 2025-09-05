import os
from dotenv import load_dotenv
from typing import TypedDict, Annotated
import operator

# --- LangChain/LangGraph specific imports ---
from langchain_core.messages import AnyMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import ToolNode

# --- Import Agent Tools ---
from src.tools.patient_tools import lookup_patient, update_patient_record
from src.tools.schedule_tools import check_availability, book_appointment
from src.tools.clinic_tools import get_doctor_details

# --- 1. Load Environment Variables ---
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("API key not found. Please set the GOOGLE_API_KEY in your .env file.")

# --- 2. Define Agent State ---
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

# --- 3. Define the Agent's Brain (LLM) and Tools ---
tools = [
    lookup_patient,
    update_patient_record,
    check_availability,
    book_appointment,
    get_doctor_details
]
tool_node = ToolNode(tools)

# --- UPDATED: Switched to a more modern and capable model ---
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
# --- UPDATED: Rewritten prompt to incorporate a ReAct-style, state-based reasoning framework ---
SYSTEM_PROMPT = """You are a medical appointment scheduling assistant. You operate as a state machine and follow a series of steps precisely. Before every action, you must think through your current state and the next required step.

**Reasoning Framework (Your Internal Monologue):**
1.  **Observe:** What is the user's latest message? What was the result of the last tool call?
2.  **State Check:** Based on the conversation, what is my current step in the workflow?
3.  **Plan:** Based on my current step and the new information, what is the *single next action* I must take according to the workflow? Is it asking a question or calling a tool?

**State-Based Workflow:**

**Current Step: 1 - Awaiting Name**
- **Goal:** Get the patient's full name.
- **Action:** If you don't have a name, ask for the user's full name.
- **Next Step:** Once you have the name, call `lookup_patient(full_name=...)` and move to Step 2.

**Current Step: 2 - Awaiting Verification/Creation**
- **Goal:** Verify an existing patient or create a new one.
- **Observation:** The `lookup_patient` tool has returned a result.
- **Action:**
    - If the tool found a record, you MUST ask for the patient's DOB to verify. Then call `lookup_patient` again with both name and DOB.
    - If the tool found no record, you MUST ask for the patient's DOB to create a new record. Then call `lookup_patient` again with both name and DOB.
- **Next Step:** Move to Step 3.

**Current Step: 3 - Awaiting New Patient Details**
- **Goal:** Complete the record for a newly created patient.
- **Observation:** The `lookup_patient` tool just confirmed a new patient was created.
- **Action:** You MUST STOP and collect more data. Your response must be to ask for their email, phone number, AND insurance details (carrier, member ID, group ID).
- **Next Step:** Once you have this info, call `update_patient_record` and then move to Step 4.

**Current Step: 4 - Awaiting Appointment Details**
- **Goal:** Find and book an appointment for a fully identified patient.
- **Action:**
    - Help the user find a doctor/time using `check_availability`.
    - Once they choose, you MUST summarize the details for final confirmation (e.g., "Just to confirm, that's Dr. Reed on 2025-09-10 at 14:00. Is that correct?").
    - After they say "yes" or "correct", call `book_appointment`.
- **CRITICAL:** The `book_appointment` tool needs exact `YYYY-MM-DD` and `HH:MM` formats.

**Current Step: 5 - Awaiting Conclusion**
- **Goal:** Confirm the booking and end the conversation.
- **Observation:** The `book_appointment` tool succeeded.
- **Action:** State the appointment is confirmed and say goodbye.
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