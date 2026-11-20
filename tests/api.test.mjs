import assert from "node:assert/strict";
import test from "node:test";
import { login, logout, getHistory, sendMessage } from "../frontend/api.js";

test("ключ передаётся только при входе, ответы 204 обрабатываются без JSON", async (t) => {
    const reply = { role: "assistant", text: "Привет" };
    const requests = [];
    const responses = [
        new Response(null, { status: 204 }), Response.json([]),
        Response.json(reply), new Response(null, { status: 204 }),
    ];
    t.mock.method(globalThis, "fetch", async (path, options) => {
        requests.push([path, options.method, options.body]);
        return responses.shift();
    });
    await login("test_key");
    assert.deepEqual(await getHistory(), []);
    assert.deepEqual(await sendMessage("Вопрос"), reply);
    await logout();
    assert.deepEqual(requests, [
        ["/api/auth/login", "POST", JSON.stringify({ key: "test_key" })],
        ["/api/messages", "GET", undefined],
        ["/api/messages", "POST", JSON.stringify({ text: "Вопрос" })],
        ["/api/auth/logout", "POST", undefined],
    ]);
});

test("ошибка сохраняет статус и сообщение API", async (t) => {
    t.mock.method(globalThis, "fetch", async () =>
        Response.json({ detail: "Требуется вход." }, { status: 401 }));
    await assert.rejects(getHistory(), { status: 401, message: "Требуется вход." });
});
