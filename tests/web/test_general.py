import urllib.parse
import html

def test_redirect(client):
    INVALID_URL = "http://www.mspaintadventures.com/ACT6ACT6.php?s=6&p=009309"
    urls = {
        "fake": INVALID_URL,
        "http://www.mspaintadventures.com/ACT6ACT6.php?s=6&p=009309": INVALID_URL,
        "https://google.com": "https://google.com",
        "http://example.com": "http://example.com",
        "/theoubliette/users/unban": INVALID_URL,
        "ftp://127.0.0.1/": INVALID_URL
    }

    for test_url, expected_url in urls.items():
        test_encoded = urllib.parse.urlencode({"url": test_url})
        rv = client.get("/redirect?" + test_encoded)

        assert rv.status_code == 200
        assert html.escape(expected_url).encode("utf8") in rv.data