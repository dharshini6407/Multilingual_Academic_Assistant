# Windows Setup Guide (PowerShell)

This guide provides simple, exact PowerShell commands for setting up, configuring, and running the **Multilingual Academic Information Assistant** on a Windows system.

---

## 📋 Prerequisites
- **Python 3.10+** (Verify with `python --version`)
- **Node.js v18+ & npm** (Verify with `node --version` and `npm --version`)
- **MySQL Server 8.0+** (Running as Windows Service `MySQL80`)

---

## ⚡ Step-by-Step PowerShell Commands

### Step 1: Open PowerShell as Administrator / User
Open PowerShell and navigate to the project directory:
```powershell
cd "c:\mini project\Multilingual_Academic_Assistant_1"
```

---

### Step 2: Configure Environment Variables
Copy `.env.example` to create `.env`:
```powershell
Copy-Item .env.example .env
Copy-Item .env.example backend\.env
```

If using MySQL, configure your credentials in `.env`:
```powershell
# Example configuration in .env:
# DB_TYPE=mysql
# MYSQL_HOST=localhost
# MYSQL_PORT=3306
# MYSQL_USER=root
# MYSQL_PASSWORD=your_actual_password
# MYSQL_DB=academic_assistant
```
*(Note: If MySQL is not configured or offline, the application automatically runs using SQLite with zero configuration required!)*

---

### Step 3: Configure MySQL Database Schema (Optional if using MySQL)
To import the production MySQL schema:
```powershell
# Using MySQL CLI:
Get-Content database\schema.sql | & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p academic_assistant
```

---

### Step 4: Setup Backend Virtual Environment & Dependencies
```powershell
# Create Python virtual environment
python -m venv backend\venv

# Activate the virtual environment
backend\venv\Scripts\Activate.ps1

# Upgrade pip and install all backend requirements
backend\venv\Scripts\pip install -r requirements.txt
```

---

### Step 5: Seed Demo Academic Data & Generate PDFs
Populates subjects, realistic attendance counts, exam countdowns, assignments, and sample academic PDFs:
```powershell
backend\venv\Scripts\python database\seed_demo_data.py
```

---

### Step 6: Setup Frontend Dependencies & Build
```powershell
cd frontend
npm install
npm run build
cd ..
```

---

### Step 7: Run Automated Verification Tests
Execute the full test suite (22 tests):
```powershell
backend\venv\Scripts\pytest -v tests
```

---

### Step 8: Start the Application

#### Terminal 1: Start Python Flask Backend (Port 5000)
```powershell
cd "c:\mini project\Multilingual_Academic_Assistant_1"
backend\venv\Scripts\python backend\app.py
```
*Backend will start on `http://127.0.0.1:5000` with APScheduler running in the Asia/Kolkata timezone.*

#### Terminal 2: Start React Frontend Dev Server (Port 5173)
```powershell
cd "c:\mini project\Multilingual_Academic_Assistant_1\frontend"
npm run dev
```

#### Terminal 3: Open in Browser
```powershell
Start-Process "http://localhost:5173"
```

---

## 🔑 Login to Explore the System

### Student Account (1-Click login available on UI):
- **Email**: `student@college.edu`
- **Password**: `Student@123`
- *Access: Multilingual Chatbot (Tamil/Tanglish/English), Live Exam Countdowns, Attendance Calculator, Study Planner, Pomodoro Timer, and Smart Alerts.*

### Administrator Account:
- **Email**: `admin@college.edu`
- **Password**: `Admin@123`
- *Access: Full Admin Control Console, PDF Knowledge Base Upload & Reindexing, Exam Schedule & Reschedule, Student Roles, and Unanswered Questions Review.*
