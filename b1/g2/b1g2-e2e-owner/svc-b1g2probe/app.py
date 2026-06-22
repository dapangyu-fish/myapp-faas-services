from flask import Flask, jsonify
import myapp_auth
app = Flask(__name__)
@app.get("/whoami")
def whoami():
    return jsonify({"caller": myapp_auth.current_user(), "authed": myapp_auth.is_authenticated()})
