from flask import Flask, request, jsonify, render_template, send_file
from dotenv import load_dotenv
import os
import pickle
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA

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
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Initialize model and parser
model = ChatGroq(model="llama-3.1-8b-instant")
parser = StrOutputParser()
history_dir = "chat_histories"

# Ensure history directory exists
if not os.path.exists(history_dir):
    os.makedirs(history_dir)

# VectorStore path
vector_store_path = "faiss_index"

# Scrape website content and create vector store
def scrape_and_create_vector_store(url):
    loader = WebBaseLoader(url)
    documents = loader.load()

    # Split large documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_documents = text_splitter.split_documents(documents)

    # Create embeddings and FAISS vector store
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_documents(split_documents, embeddings)

    # Save vector store
    vector_store.save_local(vector_store_path)
    return vector_store

# Load existing vector store or create a new one
def load_vector_store():
    if os.path.exists(f"{vector_store_path}.faiss") and os.path.exists(f"{vector_store_path}.pkl"):
        return FAISS.load_local(vector_store_path, OpenAIEmbeddings())
    else:
        return scrape_and_create_vector_store("https://www.wattlesol.com/")

# Initialize vector store
vector_store = load_vector_store()

# Retrieval chain for refining answers
retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})
retrieval_chain = RetrievalQA.from_chain_type(
    llm=model,
    retriever=retriever,
    return_source_documents=True
)

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

# Custom prompt template for Wattlesol representative
def customize_prompt(message):
    return f"""
You are a professional company representative for Wattlesol, a leading solutions provider. Respond to all queries in a polite, professional, and knowledgeable manner. Ensure that your answers are concise, accurate, and directly related to the company's services or expertise.

User query: {message}
"""

# Routes
@app.route('/chatbot-widget.js')
def serve_widget():
    return send_file('chatbot-widget.js')

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        session_id = data.get("session_id")
        message = data.get("message")

        if not session_id or not message:
            return jsonify({"error": "Session ID and message are required"}), 400

        # Retrieve session history
        history = get_session_history(session_id)

        # Add user's message to the history
        history.add_user_message(HumanMessage(content=message))

        # Customize the prompt with company representative behavior
        customized_message = customize_prompt(message)

        # Generate the response using the retrieval chain
        response = retrieval_chain.invoke({"query": customized_message}, config={"max_tokens": 300})

        # Extract the result and optionally handle the source documents
        result = response.get("result", "No response generated.")
        source_documents = response.get("source_documents", [])

        # Add the bot's response to the history
        history.add_ai_message(result)

        # Save updated history
        save_session_history(session_id, history)

        return jsonify({"response": result, "sources": [doc.page_content for doc in source_documents]})
    except Exception as e:
        print("Error occurred:", e)  # Log the error to the console
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
