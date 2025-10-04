from flask import Flask, request

app = Flask(__name__)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    return f"Authorization code received: {code}"

if __name__ == "__main__":
    app.run(port=8888)
