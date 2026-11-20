from unittest import IsolatedAsyncioTestCase

from httpx import ASGITransport, AsyncClient

from app.main import app


class FrontendTests(IsolatedAsyncioTestCase):
    async def test_root_serves_login_page(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            page = await client.get("/")
            self.assertEqual(page.status_code, 200)
            self.assertIn("text/html", page.headers["content-type"])
            self.assertIn('type="password"', page.text)
            self.assertIn('rel="stylesheet" href="/styles.css"', page.text)
            styles = await client.get("/styles.css")
            self.assertEqual(styles.status_code, 200)
            self.assertIn("text/css", styles.headers["content-type"])
