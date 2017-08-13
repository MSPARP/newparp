import re

color_validator = re.compile("^[A-Fa-f0-9]{6}$")
username_validator = re.compile("^[-a-zA-Z0-9_]+$")
url_validator = re.compile("^[-a-zA-Z0-9_]+$")
email_validator = re.compile("^.+@.+\..+$")
secret_answer_replacer = re.compile("""[!?"'(),.\s]+""")

reserved_usernames = {"admin", "charat", "msparp", "official", "staff"}

