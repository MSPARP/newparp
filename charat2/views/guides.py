import requests

def user_guide():
    r = requests.get("https://karry.terminallycapricio.us/userguide/duplicateguide.html")
    r.encoding = r.apparent_encoding
    return r.text, r.status_code

