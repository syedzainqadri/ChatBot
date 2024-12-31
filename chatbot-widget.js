(function () {
    const chatbotUrl = "http://127.0.0.1:5000"; // Replace with your backend URL
    const sessionId = `session_${Date.now()}`; // Generate a unique session ID

    // Create the toggle button for the chatbot
    const toggleButton = document.createElement("div");
    toggleButton.style.position = "fixed";
    toggleButton.style.bottom = "20px";
    toggleButton.style.right = "20px";
    toggleButton.style.width = "60px";
    toggleButton.style.height = "60px";
    toggleButton.style.background = "#533483";
    toggleButton.style.borderRadius = "50%";
    toggleButton.style.boxShadow = "0 5px 15px rgba(0, 0, 0, 0.3)";
    toggleButton.style.cursor = "pointer";
    toggleButton.style.display = "flex";
    toggleButton.style.justifyContent = "center";
    toggleButton.style.alignItems = "center";
    toggleButton.style.zIndex = "1000";
    toggleButton.innerHTML = `<span style="color: white; font-size: 24px;">💬</span>`; // Chat icon
    document.body.appendChild(toggleButton);

    // Create the widget container
    const chatbotContainer = document.createElement("div");
    chatbotContainer.id = "chatbot-widget";
    chatbotContainer.style.position = "fixed";
    chatbotContainer.style.bottom = "90px"; // Adjusted for icon position
    chatbotContainer.style.right = "20px";
    chatbotContainer.style.width = "350px";
    chatbotContainer.style.height = "500px";
    chatbotContainer.style.background = "#0f3460";
    chatbotContainer.style.borderRadius = "15px";
    chatbotContainer.style.boxShadow = "0 10px 30px rgba(0, 0, 0, 0.2)";
    chatbotContainer.style.overflow = "hidden";
    chatbotContainer.style.display = "none"; // Hidden by default
    chatbotContainer.style.flexDirection = "column";
    chatbotContainer.style.fontFamily = "Arial, sans-serif";
    document.body.appendChild(chatbotContainer);

    // Add the header
    const header = document.createElement("div");
    header.style.padding = "15px";
    header.style.background = "#533483";
    header.style.color = "white";
    header.style.textAlign = "center";
    header.style.fontSize = "16px";
    header.style.fontWeight = "bold";
    header.innerText = "ChatBot";
    chatbotContainer.appendChild(header);

    // Add the messages container
    const messagesContainer = document.createElement("div");
    messagesContainer.style.flex = "1";
    messagesContainer.style.padding = "10px";
    messagesContainer.style.overflowY = "auto";
    messagesContainer.style.background = "#0f3460";
    chatbotContainer.appendChild(messagesContainer);

    // Add the input area
    const inputContainer = document.createElement("div");
    inputContainer.style.display = "flex";
    inputContainer.style.padding = "10px";
    inputContainer.style.background = "#16213e";
    chatbotContainer.appendChild(inputContainer);

    const inputField = document.createElement("input");
    inputField.type = "text";
    inputField.placeholder = "Type your message...";
    inputField.style.flex = "1";
    inputField.style.padding = "10px";
    inputField.style.border = "none";
    inputField.style.borderRadius = "10px";
    inputContainer.appendChild(inputField);

    const sendButton = document.createElement("button");
    sendButton.innerText = "Send";
    sendButton.style.marginLeft = "10px";
    sendButton.style.padding = "10px 20px";
    sendButton.style.background = "#533483";
    sendButton.style.border = "none";
    sendButton.style.borderRadius = "10px";
    sendButton.style.color = "white";
    sendButton.style.cursor = "pointer";
    sendButton.style.transition = "background 0.3s ease";
    sendButton.addEventListener("mouseover", () => (sendButton.style.background = "#6c44b5"));
    sendButton.addEventListener("mouseout", () => (sendButton.style.background = "#533483"));
    inputContainer.appendChild(sendButton);

// Append a message to the chat
function appendMessage(sender, text = "", isTyping = false) {
    const message = document.createElement("div");
    message.style.marginBottom = "10px";
    message.style.padding = "10px";
    message.style.borderRadius = "10px";
    message.style.maxWidth = "75%";
    message.style.wordWrap = "break-word";
    message.style.color = "white";
    message.style.background = sender === "user" ? "#533483" : "#1a1a2e";
    message.style.alignSelf = sender === "user" ? "flex-end" : "flex-start";
    message.innerHTML = isTyping ? "Typing..." : text.replace(/\n/g, "<br>");
    messagesContainer.appendChild(message);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return message;
}

// Type out the bot's response character by character
function typeResponse(element, text, delay = 30) {
    let i = 0;
    element.innerHTML = ""; // Clear any placeholder text
    function typeNext() {
        if (i < text.length) {
            element.innerHTML += text[i] === "\n" ? "<br>" : text[i];
            i++;
            setTimeout(typeNext, delay);
        }
    }
    typeNext();
}

// Handle sending messages
async function sendMessage() {
    const message = inputField.value.trim();
    if (!message) return;

    // Display the user's message
    appendMessage("user", message);
    inputField.value = "";

    // Add a placeholder for the bot's response
    const botMessageElement = appendMessage("bot", "", true); // Typing indicator

    try {
        const response = await fetch(`${chatbotUrl}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message, session_id: sessionId }),
        });

        const data = await response.json();
        if (data.response) {
            // Start typing effect for bot response
            botMessageElement.innerHTML = ""; // Clear "Typing..." placeholder
            typeResponse(botMessageElement, data.response);
        } else {
            botMessageElement.innerHTML = "Sorry, I encountered an error.";
        }
    } catch (error) {
        botMessageElement.innerHTML = "Unable to connect to the server.";
    }
}


    // Toggle chatbot visibility
    toggleButton.addEventListener("click", () => {
        if (chatbotContainer.style.display === "none") {
            chatbotContainer.style.display = "flex";
        } else {
            chatbotContainer.style.display = "none";
        }
    });

    // Add event listeners
    sendButton.addEventListener("click", sendMessage);
    inputField.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            sendMessage();
        }
    });
})();
