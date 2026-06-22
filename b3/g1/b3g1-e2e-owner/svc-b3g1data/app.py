from flask import Flask
import myapp_data
app=Flask(__name__)
@app.get("/x")
def x():
    return {"ok":True}
