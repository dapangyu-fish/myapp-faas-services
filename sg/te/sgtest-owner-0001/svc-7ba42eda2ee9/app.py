from flask import Flask, jsonify
import myapp_auth
app=Flask(__name__)
@app.get("/whoami")
def w():
    me=myapp_auth.current_user()
    return jsonify({"me":me or "","logged_in":bool(me)})
