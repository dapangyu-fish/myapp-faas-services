from flask import Flask
app=Flask(__name__)
@app.get("/p")
def p():
    return {"ok":True}
