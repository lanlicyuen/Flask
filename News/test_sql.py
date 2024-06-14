import secrets

# 生成一个随机的 SECRET_KEY
SECRET_KEY = secrets.token_hex(32)
print(f"Generated SECRET_KEY: {SECRET_KEY}")