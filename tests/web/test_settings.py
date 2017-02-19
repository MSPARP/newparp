import time

# Timezone

def change_timezone(client, timezone):
    rv = client.post("/settings/timezone", data=dict(
        timezone=timezone
    ))
    return rv

def test_timezone_valid(user_client):
    rv = change_timezone(user_client, "UTC")
    assert rv.status_code in (200, 302)

def test_timezone_invalid(user_client):
    rv = change_timezone(user_client, "Poop")
    assert rv.status_code in (200, 302)

# Theme

def change_theme(client, theme):
    rv = client.post("/settings/theme", data=dict(
        theme=theme
    ))
    return rv

def test_theme_valid(user_client):
    themes = [
        "",
        "darkskin",
        "felt",
        "msparp_basic",
    ]

    for theme in themes:
        rv = change_theme(user_client, theme)
        assert rv.status_code in (200, 302)

def test_theme_invalid(user_client):
    rv = change_theme(user_client, "i tried")
    assert rv.status_code in (200, 302)