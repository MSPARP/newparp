import requests


def user_guide():
    r = requests.get("http://alpacaweb.net/guides/userguide.html")
    r.encoding = r.apparent_encoding
    return r.text, r.status_code


def bbcode_guide():
    r = requests.get("http://alpacaweb.net/guides/bbcode.html")
    r.encoding = r.apparent_encoding
    return r.text, r.status_code
