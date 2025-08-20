import uvicorn
import os

if __name__ == "__main__":
    # Change to the project root directory to ensure all paths are correct
    os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    uvicorn.run(
        "src.soft.router:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
