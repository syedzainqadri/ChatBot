import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import trim_messages
import warnings
import pickle

warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()

# Set environment variables
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = "chatbot_with_langchain"
os.environ["GROQ_API_KEY"] = os.getenv('GROQ_API_KEY')
os.environ["LANGCHAIN_API_KEY"] = os.getenv('LANGCHAIN_API_KEY')

# Initialize model and parser
model = ChatGroq(model="llama-3.1-8b-instant")
parser = StrOutputParser()

# Session history management
store = {}

def get_session_history(session_id: str):
    """Retrieve or create session history."""
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

def save_to_pickle(filename, chat_history):
    """Save chat history to a file."""
    try:
        with open(filename, 'wb') as f:
            pickle.dump(chat_history, f)
    except Exception as e:
        print(f"Error saving to pickle: {e}")

def load_from_pickle(filename):
    """Load chat history from a file."""
    try:
        with open(filename, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Error loading from pickle: {e}")
        return {}

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
chain = prompt | model
model_with_memory = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="messages",
)

# Configuration
config = {'configurable': {'session_id': 'dynamic_session'}}

def get_response(message, session_id="default"):
    """Generate a response based on user input."""
    try:
        response = model_with_memory.invoke(
            {
                "messages": [HumanMessage(content=message)],
                "language": "English",
            },
            config={'configurable': {'session_id': session_id}},
        )
        return response.content
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Sorry, I encountered an error. Please try again later."

# Main loop
if os.path.exists('data.pkl'):
    store = load_from_pickle('data.pkl')

while True:
    message = input("Write Your Query Here...: ")
    if message.strip().lower() == "bye":
        print(get_response(message))
        save_to_pickle("data.pkl", store)
        print("-" * 40)
        print("Chat history saved.")
        break
    else:
        print(get_response(message))
