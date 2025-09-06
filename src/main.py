import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from src.agent import app
import re
from datetime import datetime
from streamlit_calendar import calendar

def parse_and_display_interactive_calendar(response: str):
    """
    Parses the agent's availability response and displays a visual, interactive calendar.
    """
    lines = response.split('\n')
    
    availability = {}
    # This regex is designed to find date headers in both formats the AI might use
    date_pattern = re.compile(r"(?:---|)(.*, .* \d{1,2}, \d{4})(?: ---|:)")
    current_date_str = None

    for line in lines:
        date_match = date_pattern.search(line)
        if date_match:
            full_date_str = date_match.group(1).strip()
            try:
                current_date_str = datetime.strptime(full_date_str, '%A, %B %d, %Y').strftime('%Y-%m-%d')
                if current_date_str not in availability:
                    availability[current_date_str] = []
            except ValueError:
                current_date_str = None
            continue
        
        if ("Morning:" in line or "Afternoon:" in line) and current_date_str:
            times_str = line.split(':', 1)[1].strip()
            times = [t.strip() for t in times_str.split(',') if t.strip()]
            availability[current_date_str].extend(times)

    if not availability:
        # If parsing fails for any reason, just display the agent's raw text
        st.markdown(response)
        return

    # Create event objects for the streamlit-calendar component
    calendar_events = []
    for date_str in availability:
        calendar_events.append({
            "title": f"{len(availability[date_str])} slots",
            "start": date_str,
            "end": date_str,
            "allDay": True,
            "color": "#4CAF50", # Green color for available days
        })
    
    st.markdown("##### Click on a green date to see time slots:")
    calendar_widget = calendar(events=calendar_events, options={"headerToolbar": {"left": "today prev,next", "center": "title", "right": ""}})

    # Check if a date on the calendar was clicked
    if calendar_widget and 'dateClick' in calendar_widget:
        clicked_date = calendar_widget['dateClick']['dateStr']
        st.session_state.selected_date = clicked_date

    # If a date has been selected (and is still in session state), display its time slots as buttons
    if 'selected_date' in st.session_state and st.session_state.selected_date and st.session_state.selected_date in availability:
        selected_date_str = st.session_state.selected_date
        st.subheader(f"Available Times for {datetime.strptime(selected_date_str, '%Y-%m-%d').strftime('%A, %B %d')}:")
        times = availability[selected_date_str]
        
        cols = st.columns(5)
        for i, time in enumerate(times):
            if cols[i % 5].button(time, key=f"{selected_date_str}-{time}"):
                # When a time is clicked, set it as the user's next input and rerun the app
                st.session_state.user_input = f"I'd like to book the {time} slot on {selected_date_str}"
                st.session_state.selected_date = None # Clear the selected date to hide the buttons on the next run
                st.rerun()

def main():
    st.set_page_config(page_title="Medical Appointment AI Agent", page_icon="🤖", layout="centered")
    st.title("Medical Appointment AI Agent 🤖")
    st.write("Welcome! I can help you book a medical appointment.")

    # Initialize session state variables if they don't exist
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user_input" not in st.session_state:
        st.session_state.user_input = ""
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = None

    # Display the chat history
    for message in st.session_state.messages:
        with st.chat_message(message.type):
            # This is the robust trigger to decide when to show the interactive calendar
            if message.type == "ai" and ("Morning:" in message.content or "Afternoon:" in message.content or "---" in message.content):
                parse_and_display_interactive_calendar(message.content)
            else:
                st.markdown(message.content)

    # Get user input either from the text box or a button click
    prompt = st.chat_input("How can I help you today?")
    if st.session_state.user_input:
        prompt = st.session_state.user_input
        st.session_state.user_input = "" 

    if prompt:
        st.session_state.messages.append(HumanMessage(content=prompt))
        
        with st.spinner("Thinking..."):
            response = app.invoke({"messages": st.session_state.messages})
            ai_message = response["messages"][-1]
            st.session_state.messages.append(ai_message)
        
        # Reset the selected date after each turn to ensure a clean state
        st.session_state.selected_date = None 
        st.rerun()

if __name__ == "__main__":
    main()