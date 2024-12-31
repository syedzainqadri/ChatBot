from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import os
import pickle
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import warnings

warnings.filterwarnings("ignore")

# Initialize Flask app
app = Flask(__name__)

# Load environment variables
load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = "chatbot_with_langchain"
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")

# Initialize model and parser
model = ChatGroq(model="llama-3.1-8b-instant")
parser = StrOutputParser()
history_dir = "chat_histories"

# Ensure history directory exists
if not os.path.exists(history_dir):
    os.makedirs(history_dir)

# Session history management
def get_session_history(session_id: str):
    filepath = os.path.join(history_dir, f"{session_id}.pkl")
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            return pickle.load(f)
    return InMemoryChatMessageHistory()

def save_session_history(session_id: str, history):
    filepath = os.path.join(history_dir, f"{session_id}.pkl")
    with open(filepath, "wb") as f:
        pickle.dump(history, f)

# Prompt and trimmer
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant. Answer all questions to the best of your ability."),
        MessagesPlaceholder(variable_name="messages"),
    ]
)
chain = prompt | model
model_with_memory = RunnableWithMessageHistory(chain, get_session_history, input_messages_key="messages")

from flask import Flask, render_template, send_file

app = Flask(__name__)

# Serve chatbot-widget.js from the root directory
@app.route('/chatbot-widget.js')
def serve_widget():
    return send_file('chatbot-widget.js')

@app.route('/')
def index():
    return render_template('index.html')


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    session_id = data.get("session_id")
    message = data.get("message")
    print("message:",message)

    if not session_id or not message:
        return jsonify({"error": "Session ID and message are required"}), 400

    # Retrieve session history
    history = get_session_history(session_id)

    # Add user's message to the history
    history.add_user_message(HumanMessage(content=message))

    try:
        # Generate the response
        response = chain.invoke(
            {"messages": history.messages}, config={"configurable": {"session_id": session_id}}
        )

        # Add the bot's response to the history
        history.add_ai_message(response.content)

        # Save updated history
        save_session_history(session_id, history)
        print("BOT Response: ",response.content)
        return jsonify({"response": response.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
