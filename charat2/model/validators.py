import re

color_validator = re.compile("^[A-Fa-f0-9]{6}$")
username_validator = re.compile("^[-a-z0-9_]+$")

reserved_usernames = {
    "admin",
    "charat",
    "msparp",
    "official",
    "staff",
}

