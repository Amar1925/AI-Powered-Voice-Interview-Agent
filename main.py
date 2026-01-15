from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from langchain_community.document_loaders import PyPDFLoader
import shutil
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load Gemini API key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

app = FastAPI()

class SummaryResponse(BaseModel):
    summary: str

@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <html>
        <body>
            <h2>Upload a PDF to summarize</h2>
            <form action="/upload-and-summarize" enctype="multipart/form-data" method="post">
                <input name="file" type="file" accept=".pdf">
                <input type="submit" value="Summarize">
            </form>
        </body>
    </html>
    """

@app.post("/upload-and-summarize", response_model=SummaryResponse)
async def upload_and_summarize(file: UploadFile = File(...)):
    file_location = f"temp_{file.filename}"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        loader = PyPDFLoader(file_location)
        pages = loader.load()
        full_text = "\n".join([p.page_content for p in pages])

        prompt = f"Summarize this document:\n\n{full_text}"
        response = model.generate_content(prompt)

        return {"summary": response.text}
    finally:
        if os.path.exists(file_location):
            os.remove(file_location)
