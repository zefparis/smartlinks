from fastapi import FastAPI
import uvicorn
import sys

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    print("Starting minimal FastAPI server...")
    print(f"Python version: {sys.version}")
    print(f"FastAPI version: {__import__('fastapi').__version__}")
    print(f"Uvicorn version: {__import__('uvicorn').__version__}")
    
    try:
        uvicorn.run("minimal_test:app", host="0.0.0.0", port=8000, log_level="info")
    except Exception as e:
        print(f"Error starting server: {e}")
        raise
