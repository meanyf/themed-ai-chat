import pytest


@pytest.mark.anyio
async def test_root_serves_login_page(http_client):
    page = await http_client.get("/")
    assert page.status_code == 200
    assert "text/html" in page.headers["content-type"]
    assert 'type="password"' in page.text
    assert 'rel="stylesheet" href="/styles.css"' in page.text
    styles = await http_client.get("/styles.css")
    assert styles.status_code == 200
    assert "text/css" in styles.headers["content-type"]
    assert '<script type="module" src="/app.js?v=6">' in page.text
    assert (await http_client.get("/app.js?v=6")).status_code == 200
