from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def root():
    return "<h1>sparktrack çalışıyor ✅</h1><p>/signup ve diğerleri sonra eklenir.</p>"
