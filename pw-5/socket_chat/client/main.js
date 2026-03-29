console.log("Start script");

const ws = new WebSocket("ws://localhost:8080");

formChat.addEventListener("submit", (e) => {
  e.preventDefault();
  console.log(textField.value);
  ws.send(textField.value);
  textField.value = null;
});

ws.onopen = (e) => {
  console.log("Open WebSocket!");
};

ws.onmessage = (e) => {
  console.log(e.data);
  const text = e.data;
  const elMsg = document.createElement("pre");

  try {
    const parsed = JSON.parse(text);
    elMsg.textContent = JSON.stringify(parsed, null, 2);
    elMsg.classList.add("json-message");
  } catch {
    elMsg.textContent = text;
    elMsg.classList.add("plain-message");
  }

  subscribe.appendChild(elMsg);
};
