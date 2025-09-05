import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage

# Import the compiled agent app from our agent.py file
from src.agent import app

def main():
    """
    Main function to create and run the Streamlit web application.
    """
    # --- Streamlit Page Configuration ---
    st.set_page_config(
        page_title="Medical Appointment AI Agent",
        page_icon="🤖",
        layout="centered"
    )

    st.title("Medical Appointment AI Agent 🤖")
    st.write("Welcome! I can help you book, reschedule, or cancel a medical appointment.")

    # --- Session State Management ---
    # This is to keep the conversation history persistent across reruns
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display existing chat messages
    for message in st.session_state.messages:
        with st.chat_message(message.type):
            st.markdown(message.content)

    # --- Chat Input and Agent Invocation ---
    if prompt := st.chat_input("How can I help you today?"):
        # Add user message to session state and display it
        st.session_state.messages.append(HumanMessage(content=prompt))
        with st.chat_message("human"):
            st.markdown(prompt)

        # Get the agent's response
        with st.spinner("Thinking..."):
            # The 'app' is our compiled LangGraph agent
            # We pass the entire message history to maintain context
            response_stream = app.stream({"messages": st.session_state.messages})
            
            # Stream the response to the UI
            with st.chat_message("ai"):
                full_response = ""
                message_placeholder = st.empty()
                for chunk in response_stream:
                    if "agent" in chunk:
                        response_content = chunk["agent"]["messages"][-1].content
                        full_response += response_content
                        message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
        
        # Add the full AI response to the session state
        st.session_state.messages.append(AIMessage(content=full_response))


if __name__ == "__main__":
    main()