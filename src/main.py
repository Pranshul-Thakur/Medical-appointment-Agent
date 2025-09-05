from src.agent import app
from langchain_core.messages import HumanMessage

def main():
    """
    Main function to run the interactive chat loop for the AI agent.
    """
    print("\n--- Medical Appointment AI Agent ---")
    print("Agent is ready. Type 'exit' to end the conversation.")

    # This list will store the entire conversation history.
    conversation_history = []

    # Start an infinite loop for the chat
    while True:
        # Get input from the user
        user_input = input("You: ")

        # Check if the user wants to exit
        if user_input.lower() == 'exit':
            print("Ending conversation. Goodbye!")
            break

        # Append the user's new message to the history
        conversation_history.append(HumanMessage(content=user_input))

        # Invoke the compiled agent graph with the FULL conversation history
        final_response = None
        print("Agent: ", end="", flush=True)
        for chunk in app.stream({"messages": conversation_history}):
            # The output of the graph is a dictionary of states. We are interested in the 'agent' state.
            if "agent" in chunk:
                # The agent's response is in the 'messages' of its state
                response_messages = chunk["agent"]["messages"]
                if response_messages:
                    # The actual content is in the last message
                    final_response = response_messages[-1]
                    print(final_response.content, end="", flush=True)
        
        # Add the agent's final response to the history for the next turn
        if final_response:
            conversation_history.append(final_response)

        # Print a newline for better formatting after the agent's response
        print("\n")


if __name__ == "__main__":
    # To run the application:
    # 1. Navigate to the root directory 'ai_medical_scheduler' in your terminal.
    # 2. Run the command: python -m src.main
    main()