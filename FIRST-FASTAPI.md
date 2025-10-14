# FastAPI “Hello World” Example

A minimal FastAPI application that exposes a single `GET /` endpoint returning **Hello, world!** in JSON.

---

## Requirements

* Python 3.9 or later  
* Packages listed in `requirements.txt`

---

## Quick Start

1. **Clone the repository & create a virtual environment (optional but recommended).**
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies.**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application.**
   ```bash
   uvicorn app.main:app --reload
   ```
   * `app.main` — points to `app/main.py`
   * `app` — the FastAPI instance inside that file
   * `--reload` — auto-reloads when files change (development only)

4. **Test in your browser or by using `curl`.**
   ```bash
   curl http://127.0.0.1:8000/
   # → {"message":"Hello, world!"}
   ```

---