from fastapi import FastAPI, UploadFile, File
import tempfile, json ,os
from middleware.connectors.sqlite import SQLiteConnector
from middleware.connectors.postgres_db import PostGresConnector
from pydantic import BaseModel

app = FastAPI()


class DBConfig(BaseModel):
    username: str
    password: str
    host: str
    port: int = 5432
    database: str

@app.get("/")
def root():
    return {"message": "Hello World"}


@app.post("/sqllite")
async def extract_schema(file: UploadFile = File(...)):
    # Save upload to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        connector = SQLiteConnector(filepath=tmp_path)
        connector.connect()
        schema = connector.extract_schema()
    finally:
        os.unlink(tmp_path)  # clean up temp file

    return schema


@app.post("/postgres")
def extract_postgres_schema(config: DBConfig):
    connector = PostGresConnector(config=config.model_dump())
    connector.connect()
    schema = connector.extract_schema()
    return schema
