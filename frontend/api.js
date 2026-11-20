async function request(path, method, data) {
    const options = { method, credentials: "same-origin" };
    if (data !== undefined) {
        options.headers = { "Content-Type": "application/json" };
        options.body = JSON.stringify(data);
    }

    const response = await fetch(path, options);
    if (!response.ok) {
        const body = await response.json().catch(() => null);
        const message = typeof body?.detail === "string"
            ? body.detail
            : `Не удалось выполнить запрос (HTTP ${response.status}).`;
        const error = new Error(message);
        error.status = response.status;
        throw error;
    }

    if (response.status === 204) return;
    return response.json();
}

export function login(key) {
    return request("/api/auth/login", "POST", { key });
}

export function logout() {
    return request("/api/auth/logout", "POST");
}

export function getHistory() {
    return request("/api/messages", "GET");
}

export function sendMessage(text) {
    return request("/api/messages", "POST", { text });
}
