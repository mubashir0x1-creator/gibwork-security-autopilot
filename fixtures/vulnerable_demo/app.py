import subprocess
import sqlite3


API_KEY = "demo-secret-key-12345"

user_input = input("Enter expression: ")

result = eval(user_input)

print("Result:", result)


command = input("Enter command: ")

subprocess.run(
    command,
    shell=True,
)


username = input("Username: ")

connection = sqlite3.connect(
    "users.db"
)

query = "SELECT * FROM users WHERE username = '" + username + "'"

connection.execute(query)


def development_server():
    print("Starting development server...")


if __name__ == "__main__":
    development_server()