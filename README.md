# Cosmos Miners

## Project Overview

This is a Django based game project. The repository contains the source code for the **Cosmos Miners** application.

---

## Prerequisites

- **Python 3.13** (or any recent 3.x version)
- **Git**
- **Virtual environment** support (`venv` module, included with Python)

---

## Setup Instructions

The steps below work on **macOS** and **Windows**. Choose the appropriate commands for your OS.

### 1. Clone the repository

```bash
git clone <repository-url>
cd Cosmos-Miners
```

### 2. Create a virtual environment

#### macOS / Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

> **Note:** If you encounter an execution‑policy error on Windows, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` before activating.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

The project also uses **Pillow** for image handling. It is included in `requirements.txt`, but if you need to install it manually:

```bash
pip install Pillow
```

### 4. Apply database migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Run the development server

```bash
python manage.py runserver
```

The server will start at `http://127.0.0.1:8000/`. Open this URL in your browser to view the application.

---

## Common Issues

- **Port already in use** – Stop the existing process or run the server on a different port:
  ```bash
  python manage.py runserver 8001
  ```
- **Missing Pillow** – Install it with `pip install Pillow` as shown above.
- **Virtual environment not activating** – Ensure you are using the correct activation command for your OS.

---

## Cleaning Up

To deactivate the virtual environment, simply run:

```bash
deactivate
```

---

## .gitignore

A `.gitignore` file is provided to exclude the virtual environment and other unwanted files from version control.

---

*Happy coding!*
