from fastapi import FastAPI

app = FastAPI(title="Hello World FastAPI")

@app.get("/", tags=["root"])
async def read_root() -> dict[str, str]:
    """
    A simple health-check endpoint that returns a greeting.
    """
    return {"message": "Hello, world!"}