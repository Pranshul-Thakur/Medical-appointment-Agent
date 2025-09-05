import os
from dotenv import load_dotenv
from typing import TypedDict, Annotated
import operator

# --- LangChain/LangGraph specific imports ---
from langchain_core.messages import AnyMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import ToolNode

# --- Import Agent Tools (Simplified Set) ---
from src.tools.patient_tools import lookup_patient
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
# --- REVERTED: Using the simpler, more stable toolset ---
tools = [
    lookup_patient,
    check_availability,
    book_appointment,
    get_doctor_details
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
# --- REVERTED: Using a simpler prompt with a highly specific rule for the point of failure ---
SYSTEM_PROMPT = """You are a helpful and friendly medical appointment scheduling assistant. Your primary purpose is to help patients book appointments with doctors.

**Your Workflow:**
1.  **Greet & Gather Info:** Greet the user. Get their full name and date of birth in `YYYY-MM-DD` format.
2.  **Lookup Patient:** Use the `lookup_patient` tool.
3.  **Find & Book:**
    - Use `get_doctor_details` or `check_availability` to help the user find a doctor and time slot.
    - When the user chooses a final time, use the `book_appointment` tool.
    - **CRITICAL EXECUTION RULE:** The `book_appointment` tool has very strict arguments. You MUST provide the `appointment_date` as a `YYYY-MM-DD` string and `appointment_time` as an `HH:MM` string.
        - Example: If the user says "Sept 8th at 2pm", you must call the tool with `appointment_date="2025-09-08"` and `appointment_time="14:00"`.
        - You MUST find the `patient_id` and `patient_status` from earlier in the conversation history to use in the tool call.
4.  **Conclude:** After `book_appointment` succeeds, confirm the booking and say goodbye.
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