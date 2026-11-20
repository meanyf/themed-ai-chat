import { getHistory, login, logout } from "./api.js";

const startup = document.querySelector("#startup");
const status = document.querySelector("#startup-status");
const retry = document.querySelector("#retry-history");
const loginScreen = document.querySelector("#login-screen");
const chatScreen = document.querySelector("#chat-screen");
const messages = document.querySelector("#messages");

async function loadHistory() {
    loginScreen.hidden = true;
    startup.hidden = false;
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
        document.querySelector("#message-text").value = "";
        showLogin();
    } catch {
        logoutError.textContent = "Не удалось выйти. Попробуйте снова.";
    } finally {
        logoutButton.disabled = false;
    }
});

retry.addEventListener("click", loadHistory);
loadHistory();
