const questions = {{ questions | tojson }};
let qIndex = 0;

const messagesDiv = document.getElementById('chatbot-messages');
const input = document.getElementById('chatbot-input');
const sendBtn = document.getElementById('chatbot-send');

function appendMessage(text, sender='bot') {
    const p = document.createElement('p');
    p.textContent = text;
    p.style.fontWeight = sender === 'bot' ? 'bold' : 'normal';
    messagesDiv.appendChild(p);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

async function sendAnswer(answer) {
    const response = await fetch('/chatbot/next', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({answer})
    });
    const data = await response.json();

    if (data.done) {
        appendMessage(data.message);
        input.disabled = true;
        sendBtn.disabled = true;
    } else {
        appendMessage(data.question);
        qIndex++;
    }
}

sendBtn.addEventListener('click', () => {
    const answer = input.value.trim();
    if (!answer) return;
    appendMessage(answer, 'user');
    input.value = '';
    sendAnswer(answer);
});

input.addEventListener('keypress', e => {
    if (e.key === 'Enter') {
        sendBtn.click();
    }
});

// İlk soruyu göster
window.onload = () => {
    if (questions.length > 0) {
        appendMessage(questions[0]);
    }
};
