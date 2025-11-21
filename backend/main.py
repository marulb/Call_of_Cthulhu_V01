from fastapi import FastAPI

app = FastAPI(title="Call of Cthulhu API")

@app.get("/")
async def root():
    return {"message": "Call of Cthulhu API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
