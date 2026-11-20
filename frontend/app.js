import { getHistory } from "./api.js";

const startup = document.querySelector("#startup");
const status = document.querySelector("#startup-status");
const retry = document.querySelector("#retry-history");
const loginScreen = document.querySelector("#login-screen");
const chatScreen = document.querySelector("#chat-screen");
const messages = document.querySelector("#messages");

async function loadHistory() {
    retry.hidden = true;
    status.textContent = "Загрузка истории…";
    try {
        const history = await getHistory();
        messages.replaceChildren(...history.map(message => {
            const item = document.createElement("li");
            item.textContent = message.text;
            return item;
        }));
        startup.hidden = true;
        chatScreen.hidden = false;
    } catch (error) {
        if (error.status === 401) {
            startup.hidden = true;
            loginScreen.hidden = false;
            document.querySelector("#access-key").focus();
            return;
        }
        status.textContent = "Не удалось загрузить историю.";
        retry.hidden = false;
    }
}

retry.addEventListener("click", loadHistory);
loadHistory();
