import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, trim_messages
from operator import itemgetter
from langchain_core.runnables import RunnablePassthrough
import warnings
import pickle
# import logging

warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = "true"

os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

os.environ["LANGCHAIN_PROJECT"] = "chatbot_with_langchain"

os.environ["GROQ_API_KEY"] = os.getenv('GROQ_API_KEY')

model = ChatGroq(model="llama-3.1-8b-instant")

# Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')÷

# Initialize model and parser
model = ChatGroq(model="llama-3.1-8b-instant")
parser = StrOutputParser()

# Session history management
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


def save_to_pickle(filename, chat_history):
    with open(filename, 'wb') as f:
        pickle.dump(chat_history, f)

def load_from_pickle(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

# Prompt and trimmer
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant. Answer all questions to the best of your ability."),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

trimmer = trim_messages(
    max_tokens=5000,
    strategy="last",
    token_counter=model,
    include_system=True,
    allow_partial=False,
    start_on="human",
)

# Chain and model with memory
chain = (
    RunnablePassthrough.assign(messages=itemgetter("messages") | trimmer)
    | prompt
    | model
)

model_with_memory = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="messages",
)

# Configuration
config = {'configurable': {'session_id': 'Firstchat'}}

def get_response(message):
    try:
        response = model_with_memory.invoke(
            {
                "messages": [HumanMessage(content=message)],
                "language": "English",
            },
            config=config,
        )
        return response.content
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Sorry, I encountered an error. Please try again later."


if os.path.exists('data.pkl'):
    store = load_from_pickle('data.pkl')

import streamlit as st

st.title("CHat BOT")
st.header("CHat Bot For You")
i = 1
import time
message = st.text_input("YOur  QUery here")
if message:
    if 'bye' in message.lower():
        st.write(get_response(message))
        time.sleep(5)
        st.stop()
    else:
        st.write(get_response(message))
        
