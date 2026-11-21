import { getHistory, login, logout } from "./api.js";

const startup = document.querySelector("#startup");
const status = document.querySelector("#startup-status");
const retry = document.querySelector("#retry-history");
const loginScreen = document.querySelector("#login-screen");
const chatScreen = document.querySelector("#chat-screen");
const messages = document.querySelector("#messages");

const emptyHistory = document.querySelector("#empty-history");
const messageText = document.querySelector("#message-text");
const dateFormat = new Intl.DateTimeFormat("ru-RU", { dateStyle: "medium", timeStyle: "short" });

for (const example of emptyHistory.querySelectorAll("button")) {
    example.addEventListener("click", () => {
        messageText.value = example.textContent;
        messageText.dispatchEvent(new Event("input", { bubbles: true }));
        messageText.focus();
    });
}

function renderMessage(message) {
    const item = document.createElement("li");
    item.dataset.role = message.role;
    const author = document.createElement("strong");
    author.textContent = message.role === "user" ? "Пользователь" : "Помощник";
    const time = document.createElement("time");
    time.dateTime = message.created_at;
    time.textContent = dateFormat.format(new Date(message.created_at));
    const text = document.createElement("p");
    text.textContent = message.text;
    item.append(author, time, text);
    return item;
}

function renderHistory(history) {
    const position = messages.scrollTop;
    const atBottom = messages.scrollHeight - messages.clientHeight - position < 2;
    messages.hidden = history.length === 0;
    emptyHistory.hidden = history.length > 0;
    messages.replaceChildren(...history.map(renderMessage));
    messages.scrollTop = atBottom ? messages.scrollHeight : position;
}

async function loadHistory() {
    loginScreen.hidden = true;
    startup.hidden = false;
    retry.hidden = true;
    status.textContent = "Загрузка истории…";
    try {
        const history = await getHistory();
        startup.hidden = true;
        chatScreen.hidden = false;
        renderHistory(history);
    } catch (error) {
        if (error.status === 401) {
            showLogin();
            return;
        }
        status.textContent = "Не удалось загрузить историю.";
        retry.hidden = false;
    }
}

const key = document.querySelector("#access-key");
const toggle = document.querySelector("#toggle-key");
const submit = document.querySelector("#login-submit");
const loginError = document.querySelector("#login-error");
const logoutButton = document.querySelector("#logout");
const logoutError = document.querySelector("#logout-error");

function updateLogin() {
    const valid = /^[A-Za-z0-9_-]{8,255}$/.test(key.value);
    submit.disabled = key.readOnly || !valid;
    loginError.textContent = key.value && !valid ? "Проверьте длину и допустимые символы ключа." : "";
}

function showLogin() {
    startup.hidden = true;
    chatScreen.hidden = true;
    loginScreen.hidden = false;
    updateLogin();
    key.focus();
}

key.addEventListener("input", updateLogin);
toggle.addEventListener("click", () => {
    const reveal = key.type === "password";
    key.type = reveal ? "text" : "password";
    toggle.textContent = reveal ? "Скрыть" : "Показать";
});

document.querySelector("#login-form").addEventListener("submit", async event => {
    event.preventDefault();
    updateLogin();
    if (submit.disabled) return;
    key.readOnly = true;
    submit.disabled = true;
    try {
        await login(key.value);
    } catch (error) {
        key.readOnly = false;
        updateLogin();
        loginError.textContent = error.status === 401 ? "Неверный ключ доступа." : "Не удалось войти. Попробуйте снова.";
        key.focus();
        return;
    }
    key.value = "";
    key.type = "password";
    toggle.textContent = "Показать";
    key.readOnly = false;
    await loadHistory();
});

logoutButton.addEventListener("click", async () => {
    if (logoutButton.disabled) return;
    logoutButton.disabled = true;
    logoutError.textContent = "";
    try {
        await logout();
        messages.replaceChildren();
        messageText.value = "";
        showLogin();
    } catch {
        logoutError.textContent = "Не удалось выйти. Попробуйте снова.";
    } finally {
        logoutButton.disabled = false;
    }
});

retry.addEventListener("click", loadHistory);
loadHistory();
