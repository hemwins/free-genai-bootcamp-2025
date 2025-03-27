# Japanese Teaching Assistant

This application is a chat agent built using Streamlit and Amazon Bedrock. It allows users to interact with a conversational agent designed to assist with Japanese language learning.

## Workflow

1. **User Interaction**: Users input their queries through a chat interface provided by Streamlit.
2. **Message Handling**: The application maintains a session state to keep track of the conversation history.
3. **Query Processing**: User inputs are sent to Amazon Bedrock for processing. The application uses an asynchronous function to handle communication with the Bedrock API.
4. **Response Generation**: Bedrock processes the input and returns a response, which is then displayed to the user in the chat interface.

## Technologies Used

- **Streamlit**: Provides the web interface for user interaction.
- **Amazon Bedrock**: Used as the backend for natural language processing.
- **Python Asyncio**: Manages asynchronous tasks to ensure smooth interaction.

## Model Information

- **Amazon Nova**: `amazon.nova-lite-v1:0`
- **Command R**:
  - `cohere.command-r-plus-v1:0`
  - `cohere.command-light-text-v14`
  - `cohere.command-r-v1:0`

## Setup Instructions

1. Install the required packages:
   ```sh
   pip install -r requirements.txt
   ```
2. Run the application:
   ```sh
   streamlit run app.py
   ```
