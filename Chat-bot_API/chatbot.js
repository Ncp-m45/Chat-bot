const chatInput = document.querySelector(".chat-input textarea");
const sendChatBtn = document.querySelector(".chat-input span");
const chatbox = document.querySelector(".chatbox");
const chatbotToggler = document.querySelector(".chatbot-toggler")

let userMessage;

const createChatLi = (message , className)=>{
    //สร้างแชท <li> element ผ่าน message และ className
    const chatLi = document.createElement("li");
    chatLi.classList.add("chat",className);
    let chatContent = className === "outgoing" ? `<p></p>`: `<span class="material-symbols-outlined">smart_toy</span><p></p>`;
    chatLi.innerHTML = chatContent;
    chatLi.querySelector('p').textContent = message;
    return chatLi;
}

const generateResponse = (incomingChatLi) => {
    const API_URL = "http://localhost:5000/chat"; // Flask API endpoint
    const messageElement = incomingChatLi.querySelector("p");

    const requestOptions = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            question: userMessage
        })
    };

    fetch(API_URL, requestOptions).then(res => res.json()).then(data => {
        if (data.response) {
            messageElement.textContent = data.response;
        } else {
            messageElement.textContent = "Oops! Something went wrong. Please try again.";
        }
    }).catch(() => {
        messageElement.textContent = "Oops! Something went wrong. Please try again.";
    }).finally(() => chatbox.scrollTo(0, chatbox.scrollHeight));
}

const handleChat = ()=>{
    userMessage = chatInput.value.trim();
    if(!userMessage) return;
    chatInput.value = ""

    //เพิ่มข้อความของ user ไปที่ chatbox
    chatbox.appendChild(createChatLi(userMessage , 'outgoing'));
    chatbox.scrollTo(0,chatbox.scrollHeight);

    setTimeout(()=>{
        const incomingChatLi = createChatLi("Thinking..." , 'incoming');
        chatbox.appendChild(incomingChatLi);
        chatbox.scrollTo(0,chatbox.scrollHeight);
        generateResponse(incomingChatLi);
    },600)
}


sendChatBtn.addEventListener("click",handleChat);
// chatbotToggler.addEventListener("click", () => document.body.classList.toggle("show-chatbot"));
chatbotToggler.addEventListener("click", () => {
    document.querySelector("#show-chatbot").classList.toggle("show-chatbot");
});