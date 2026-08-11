# ✍️ WriteRightBE

**WriteRight** is an AI-powered language learning journal that helps learners improve their writing by analyzing journal entries, correcting grammar, and explaining mistakes in a way that's easy to understand.

---

## ✨ Features

- 📝 Write journal entries in your target language
- 🤖 AI-powered grammar and spelling corrections
- 💡 Explanations for why corrections were made
- 📚 Learn from your mistakes as you write

---

## 🛠 Tech Stack

### Backend
- Python
- FastAPI

---

# 🚀 Getting Started


## Backend Setup

Navigate to the backend project (`write-right-be`).

### Create a virtual environment

```bash
python3 -m venv .venv
```

### Activate the virtual environment

**macOS / Linux**

```bash
source .venv/bin/activate
```

**Windows (Command Prompt)**

```cmd
.venv\Scripts\activate
```

**Windows (PowerShell)**

```powershell
.venv\Scripts\Activate.ps1
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Start the backend server

```bash
fastapi dev main.py
```

---

### Additional Testing Commands
```bash
python -m pytest -q
```

## 🎯 Project Goal

WriteRight is designed to make language practice more effective by giving learners immediate, personalized feedback on their writing. Instead of only correcting mistakes, the app explains *why* changes were made so users can build lasting language skills.

## For Contributors
Project Helpdesk https://notebook.google.com/notebook/cc01e95b-c671-4821-a71d-43766208983b

## Deployment Link
[write-right-be.vercel.app](https://write-right-be.vercel.app/)
