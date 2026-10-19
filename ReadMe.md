# JobLock — Setup and Run Guide

This guide covers how to run JobLock in its current state: a frontend for uploading resumes, a Flask backend for extracting PDF/DOCX text, and job retrieval through configured Greenhouse job boards.

## 1. Project structure


```text
JobLock/
├── index.html
├── style.css
└── backend/
    ├── app.py
    ├── greenhouse_boards.json
    └── .venv/
```

## 2. Prerequisites

- Python 3
- VS Code or another code editor
- A modern web browser
- The VS Code Live Server extension, if you use it to run the frontend

Check your Python installation:

```bash
python3 --version
```

## 3. Set up the Python backend

Open a terminal in the project folder and enter the backend directory:

```bash
cd backend
```

Create a virtual environment if you haven't already:

```bash
python3 -m venv .venv
```

Activate it on macOS:

```bash
source .venv/bin/activate
```

Install the required dependencies:

```bash
python -m pip install Flask flask-cors PyMuPDF python-docx requests
or pip install -r requirements.txt
```

These packages provide the Flask server, cross-origin request support, PDF/DOCX text extraction, and HTTP requests to Greenhouse.

You only need to create the environment and install dependencies initially. When opening a new terminal later, activate the environment again.

## 4. Configure job boards

Create or edit `backend/greenhouse_boards.json`:

```json
[
  {
    "company": "Stripe",
    "token": "stripe"
  }
]
```

Each entry represents a company and its Greenhouse board token.

**Important:** JobLock currently retrieves jobs only from the boards listed in this file. It does not search every job on the internet.

## 5. Start the backend

From the `backend/` directory, activate the environment and run:

```bash
source .venv/bin/activate
python app.py
```

The Flask backend runs on port `5000`. Keep this terminal open while using the website.

To stop the backend, press `Ctrl+C`.

### Verify the backend

Visit:

http://127.0.0.1:5000/healthcheck

Expected response:

```json
{
  "status": "ok"
}
```

## 6. Start the frontend

In VS Code:

1. Open your JobLock project folder.
2. Right-click `index.html`.
3. Select **Open with Live Server**.
4. Open the local URL that Live Server provides.

Keep both the frontend and backend running. The frontend should send API requests to:

```text
http://127.0.0.1:5000
```


## 7. Upload and process a resume

The current workflow is:

1. Select a PDF or DOCX resume.
2. Submit it through the frontend.
3. The frontend sends the file under the form field `resume`.
4. Flask validates the file extension and enforces a 5 MB limit.
5. Flask extracts the resume text in memory.
6. The `/search-jobs` endpoint fetches jobs from the configured Greenhouse boards.
7. Flask returns the resume text and job listings as JSON.
8. The frontend uses the returned information to match and display jobs.

The backend currently provides these routes:

| Route | Method | Purpose |
|---|---|---|
| `/healthcheck`