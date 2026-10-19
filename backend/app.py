

from flask import Flask, request, jsonify
from flask_cors import CORS
import fitz  # PyMuPDF
from docx import Document
from io import BytesIO
from pathlib import Path
import json
import requests

ALLOWED_EXTENSIONS = {"pdf", "docx"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

app = Flask(__name__)
CORS(app)  # Allows requests from your frontend during development


# --------------------------------------------------
# Resume extraction helper
# --------------------------------------------------

def extract_resume_text(resume):
    """Validate an uploaded resume and extract its text."""

    if not resume or not resume.filename:
        return None, None, "Please upload a resume.", 400

    filename = resume.filename
    extension = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if extension not in ALLOWED_EXTENSIONS:
        return None, None, "Unsupported file type. Upload a PDF or DOCX.", 415

    try:
        file_data = resume.stream.read(MAX_FILE_SIZE + 1)

        if not file_data:
            return None, None, "The uploaded file is empty.", 400

        if len(file_data) > MAX_FILE_SIZE:
            return None, None, "Resume must be 5 MB or smaller.", 413

        if extension == "pdf":
            with fitz.open(stream=file_data, filetype="pdf") as pdf:
                text = "\n".join(page.get_text() for page in pdf)
        else:
            document = Document(BytesIO(file_data))
            paragraphs = [paragraph.text for paragraph in document.paragraphs]
            text = "\n".join(paragraphs)

        text = text.strip()

        if not text:
            return (
                None,
                None,
                "No text could be extracted. The resume may be scanned or image-based.",
                422,
            )

        return filename, text, None, 200

    except Exception:
        app.logger.exception("Resume extraction failed")
        return (
            None,
            None,
            "Unable to read this resume. Please try another file.",
            400,
        )


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.route("/healthcheck", methods=["GET"])
def healthcheck():
    return jsonify({"status": "ok"}), 200


# --------------------------------------------------
# Resume upload endpoint
# --------------------------------------------------

@app.route("/upload-resume", methods=["POST"])
def upload_resume():
    resume = request.files.get("resume")
    filename, text, error, status_code = extract_resume_text(resume)

    if error:
        return jsonify({"error": error}), status_code

    return jsonify({
        "filename": filename,
        "text": text,
        "characters": len(text),
        "message": "Resume text extracted successfully.",
    }), 200


# --------------------------------------------------
# Greenhouse job fetching
# --------------------------------------------------

def fetch_greenhouse_jobs():
    """Fetch jobs from the Greenhouse boards configured in greenhouse_boards.json."""

    boards_file = Path(__file__).parent / "greenhouse_boards.json"

    with open(boards_file, "r", encoding="utf-8") as file:
        boards = json.load(file)

    all_jobs = []
    seen_jobs = set()

    for board in boards:
        company = board["company"]
        token = board["token"]

        url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"

        try:
            response = requests.get(
                url,
                params={"content": "true"},
                timeout=15,
            )
            response.raise_for_status()

            jobs = response.json().get("jobs", [])

            for job in jobs:
                job_id = (token, job.get("id"))

                if job_id in seen_jobs:
                    continue

                seen_jobs.add(job_id)
                job["company_name"] = company
                all_jobs.append(job)

        except requests.RequestException as error:
            app.logger.warning(
                "Could not fetch jobs from %s: %s",
                company,
                error,
            )
        except ValueError as error:
            app.logger.warning(
                "Invalid response from Greenhouse board %s: %s",
                company,
                error,
            )

    return all_jobs


# --------------------------------------------------
# Job search endpoint
# --------------------------------------------------

@app.route("/search-jobs", methods=["POST"])
def search_jobs():
    """Extract the resume and return jobs for the frontend to match."""

    resume = request.files.get("resume")
    filename, text, error, status_code = extract_resume_text(resume)

    if error:
        return jsonify({"error": error}), status_code

    try:
        jobs = fetch_greenhouse_jobs()

        return jsonify({
            "filename": filename,
            "text": text,
            "characters": len(text),
            "jobs": jobs,
            "job_count": len(jobs),
            "message": (
                "Resume processed and jobs retrieved."
                if jobs
                else "Resume processed, but no jobs were retrieved. Check your configured Greenhouse boards."
            ),
        }), 200

    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        app.logger.exception("Unable to load Greenhouse board configuration")
        return jsonify({
            "error": (
                "Unable to load the job board configuration. "
                "Check backend/greenhouse_boards.json."
            )
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
