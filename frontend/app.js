import { getHistory, login, logout, sendMessage } from "./api.js";

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
    if (message.id) item.dataset.id = message.id;
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

function isHistoryAtBottom() {
    return messages.scrollHeight - messages.clientHeight - messages.scrollTop < 2;
}

function renderHistory(history) {
    const position = messages.scrollTop;
    const atBottom = isHistoryAtBottom();
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
        if (pendingCheck) finishHistoryCheck(history);
        else renderHistory(history);
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
        pendingCheck = null;
        syncButton.hidden = true;
        messageText.value = "";
        sendStatus.textContent = "";
        updateComposer();
        showLogin();
    } catch {
        logoutError.textContent = "Не удалось выйти. Попробуйте снова.";
    } finally {
        logoutButton.disabled = false;
    }
});

const messageForm = document.querySelector("#message-form");
const sendButton = document.querySelector("#send-button");
const count = document.querySelector("#message-count");
const sendStatus = document.querySelector("#send-status");
const maxLength = 500;
let sending = false;
let pendingCheck = null;
const syncButton = document.querySelector("#sync-history");

function finishHistoryCheck(history) {
    const { text, lastId, modelFailed } = pendingCheck;
    const boundary = history.findIndex(message => message.id === lastId);
    const candidates = history.slice(boundary + 1).filter(message =>
        message.role === "user" && message.text === text);
    renderHistory(history);
    if (candidates.length === 1 && (!lastId || boundary >= 0)) {
        if (messageText.value === text) messageText.value = "";
        sendStatus.textContent = "Вопрос есть в истории.";
        if (modelFailed) {
            const item = Array.from(messages.children).find(row => row.dataset.id === candidates[0].id);
            const note = document.createElement("p");
            note.textContent = "Не удалось получить ответ.";
            item.append(note);
        }
    } else {
        sendStatus.textContent = "История обновлена. Проверьте переписку перед повторной отправкой.";
    }
    pendingCheck = null;
    syncButton.hidden = true;
    updateComposer();
}

async function checkHistory() {
    syncButton.disabled = true;
    try {
        const check = pendingCheck;
        const history = await getHistory();
        if (check && pendingCheck === check) finishHistoryCheck(history);
    } catch (error) {
        if (error.status === 401) {
            showLogin();
        } else {
            sendStatus.textContent = "Пока не удалось проверить, сохранился ли вопрос.";
            syncButton.hidden = false;
        }
    } finally {
        syncButton.disabled = false;
    }
}

syncButton.addEventListener("click", checkHistory);

function updateComposer() {
    const text = messageText.value;
    const length = Array.from(text).length;
    count.textContent = `${length}/${maxLength}`;
    sendButton.disabled = sending || Boolean(pendingCheck) || length > maxLength || !text.trim();
}

messageText.addEventListener("input", updateComposer);
messageText.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
        event.preventDefault();
        if (!event.repeat && !sendButton.disabled) messageForm.requestSubmit();
    }
});

messageForm.addEventListener("submit", async event => {
    event.preventDefault();
    updateComposer();
    if (sendButton.disabled || logoutButton.disabled) return;

    const text = messageText.value;
    const lastId = messages.lastElementChild?.dataset.id;
    sending = true;
    logoutButton.disabled = true;
    messageText.readOnly = true;
    messageText.value = "";
    emptyHistory.hidden = true;
    messages.hidden = false;
    const question = renderMessage({ role: "user", text, created_at: new Date().toISOString() });
    const waiting = document.createElement("li");
    const progress = document.createElement("span");
    progress.setAttribute("role", "status");
    waiting.append(progress);
    const scrollToQuestion = isHistoryAtBottom();
    messages.append(question, waiting);
    progress.textContent = "Помощник отвечает…";
    if (scrollToQuestion) messages.scrollTop = messages.scrollHeight;
    updateComposer();
    sendStatus.textContent = "";
    try {
        const reply = await sendMessage(text);
        const scrollToReply = isHistoryAtBottom();
        waiting.replaceWith(renderMessage(reply));
        if (scrollToReply) messages.scrollTop = messages.scrollHeight;
    } catch (error) {
        waiting.remove();
        question.remove();
        messages.hidden = messages.children.length === 0;
        emptyHistory.hidden = !messages.hidden;
        messageText.value = text;
        if (error.status === 401) {
            sendStatus.textContent = "";
            showLogin();
        } else if (!error.status || error.status >= 500) {
            pendingCheck = { text, lastId, modelFailed: error.status === 502 };
            sendStatus.textContent = "Проверяем историю…";
            await checkHistory();
        } else {
            sendStatus.textContent = error.message;
        }
    } finally {
        sending = false;
        logoutButton.disabled = false;
        messageText.readOnly = false;
        updateComposer();
        if (!chatScreen.hidden) messageText.focus();
    }
});

updateComposer();
retry.addEventListener("click", loadHistory);
loadHistory();
