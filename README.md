# Power Split Bill Backend

This is the backend API service for the Power Split Bill application. It handles receipt image processing using Tesseract OCR, manages database records for bills and participants, and executes the logic for splitting costs including tax and service charges.

## Technology Stack

* **Language:** Python 3.9+
* **Framework:** FastAPI
* **OCR Engine:** Tesseract OCR
* **Database:** PostgreSQL (Production) / SQLite (Local)
* **Deployment:** Docker / Render

## System Requirements

Before running the project, ensure you have the following installed on your system:

1.  **Python 3.9** or higher.
2.  **Git**.
3.  **Tesseract OCR** (System Dependency):
    * **Windows:** Download and install from UB-Mannheim Tesseract GitHub. Add the installation path to your System PATH variables.
    * **macOS:** `brew install tesseract`
    * **Linux:** `sudo apt-get install tesseract-ocr`

## Installation Guide

Follow the steps below based on your operating system to set up the project.

### Option A: Setup for Windows

```powershell
1. Clone the repository
git clone [https://github.com/Mantossx/power-split-backend.git](https://github.com/Mantossx/power-split-backend.git)
cd power-split-backend

2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

3. Install Python dependencies
pip install -r requirements.txt
```

### Option B: Setup for macOS / Linux

```powershell

1. Clone the repository
git clone [https://github.com/Mantossx/power-split-backend.git](https://github.com/Mantossx/power-split-backend.git)
cd power-split-backend

2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

3. Install Python dependencies
pip install -r requirements.txt
```

## Running the Server
```
uvicorn app.main:app --reload
```
