import os
import json
import streamlit as st
import boto3
import asyncio
from dotenv import load_dotenv
load_dotenv()

bedrock = boto3.client('bedrock-runtime')

async def query_bedrock(chat_history):
  # open the system prompt file on every query
  script_dir = os.path.dirname(os.path.abspath(__file__))
  prompt_file_path = os.path.join(script_dir, 'prompts', 'system_prompt.md')
  with open(prompt_file_path, 'r') as file:
    system_prompt = file.read()

  model_id = os.environ.get("MODEL_ID")
  if not model_id:
    st.error("MODEL_ID not found in environment variables.")
    return "Error: MODEL_ID is not set."

  # Convert messages format to expected format for Amazon Bedrock
  messages = []
  for msg in chat_history:
    messages.append({
      "role": msg["role"],
      "content": [{"text": msg["content"] }]
    })

  #resp = bedrock.converse_stream(
  resp = await asyncio.to_thread(bedrock.converse,
    modelId=model_id,
    messages=messages,
    system=[{"text": system_prompt}]
  )
  #text = stream(resp)
  text = resp['output']['message']['content'][0]['text']
  # print(text)
  return text

st.title("Chat with Bedrock Agent")

# Set the default messages state to an empty array
if "messages" not in st.session_state:
  st.session_state.messages = []

# Render the markdown content to HTML
for msg in st.session_state.messages:
  with st.chat_message(msg["role"]):
    st.markdown(msg["content"])

async def main():
  if prompt := st.chat_input("Say something"):
      # append the user's input to the message history
      st.session_state.messages.append({"role": "user", "content": prompt})
      
      # and render it as markdown content.
      with st.chat_message("user"):
        st.markdown(prompt)
      
      with st.chat_message("assistant"):
        message_placeholder = st.empty()
        dots = ""
        response_task = asyncio.create_task(query_bedrock(st.session_state.messages))
        while not response_task.done():
          dots += "."
          message_placeholder.markdown(dots + "▌")
          await asyncio.sleep(0.5)
          if len(dots) > 3:
            dots = ""
        full_response = await response_task
        message_placeholder.markdown(full_response)
      
      st.session_state.messages.append({"role": "assistant", "content": full_response})

asyncio.run(main())
