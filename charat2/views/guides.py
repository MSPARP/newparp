import requests

def user_guide():
    r = requests.get("http://drweeaboo.net/msparp/userguide/duplicateguide.html")
    return r.text, r.status_code

