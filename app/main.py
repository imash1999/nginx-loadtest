import os, time, socket
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import create_engine, text

app = FastAPI(title="LoadTest App")
Instrumentator().instrument(app).expose(app)

DB_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin123@postgres:5432/loadtest")
engine = create_engine(DB_URL, pool_size=10, max_overflow=20)

@app.on_event("startup")
def startup():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS requests (
                id SERIAL PRIMARY KEY,
                worker VARCHAR(50),
                ts TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()

@app.get("/")
def root():
    return {"status": "ok", "worker": socket.gethostname()}

@app.get("/heavy")
def heavy():
    # CPU интенсивная задача вместо sleep
    result = sum(i*i for i in range(100000))
    with engine.connect() as conn:
        conn.execute(text("INSERT INTO requests (worker) VALUES (:w)"),
                     {"w": socket.gethostname()})
        conn.commit()
    return {"worker": socket.gethostname(), "result": result % 1000}

@app.get("/stats")
def stats():
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT worker, COUNT(*) as cnt FROM requests GROUP BY worker ORDER BY cnt DESC"
        ))
        return {"distribution": [dict(r._mapping) for r in result]}

@app.get("/health")
def health():
    return {"status": "ok"}
