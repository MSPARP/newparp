import requests


def user_guide():
    r = requests.get("https://guides.draculcorp.com/user/userguide.html")
    r.encoding = r.apparent_encoding
    return r.text, r.status_code


def bbcode_guide():
    r = requests.get("https://guides.draculcorp.com/bbcode/bbcode.html")
    r.encoding = r.apparent_encoding
    return r.text, r.status_code
