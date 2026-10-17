# generate secret key

import secrets

key = secrets.token_bytes(32)

with open("secret.key", "wb") as f:
    f.write(key)

print("Generated secret.key")