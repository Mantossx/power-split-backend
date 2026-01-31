# Power Split Bill(Backend)

The robust backend API for the Power Split Bill application. This service handles image processing (OCR), data persistence, and complex splitting logic.

##Tech Stack
- **Framework:** FastAPI (Python)
- **OCR Engine:** Tesseract OCR
- **Database:** PostgreSQL (Production) / SQLite (Local)
- **ORM:** SQLAlchemy
- **Deployment:** Docker support included

##Key Features
- **OCR Scanning:** Extracts menu items and prices from receipt images.
- **Bill Management:** Create, Read, Update, and Delete (CRUD) bills.
- **Smart Calculation:** Handles tax, service charge, and splitting logic.
- **History System:** Tracks past bills with hard-reset capability.

##How to Run Locally

1. **Clone the repository**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/power-split-backend.git](https://github.com/YOUR_USERNAME/power-split-backend.git)
   cd power-split-backend
