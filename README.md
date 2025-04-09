[![ML-Client-CI](https://github.com/software-students-spring2025/4-containers-okay-cool/actions/workflows/ml-client-ci.yml/badge.svg)](https://github.com/software-students-spring2025/4-containers-okay-cool/actions/workflows/ml-client-test.yml)
[![Web-App-CI](https://github.com/software-students-spring2025/4-containers-okay-cool/actions/workflows/web-app-ci.yml/badge.svg)](https://github.com/software-students-spring2025/4-containers-okay-cool/actions/workflows/web-app-test.yml)
![Lint-free](https://github.com/nyu-software-engineering/containerized-app-exercise/actions/workflows/lint.yml/badge.svg)
# Containerized App Exercise

# SmartGate Web App 🚪📷

## 📄 Project Description

SmartGate is a containerized web application that integrates facial recognition and attendance tracking using a machine learning client. Built with Flask, MongoDB, and DeepFace, the system allows seamless sign-ins using camera images and admin-side user management.

This project is split into two major subsystems:
- **Web App (Flask + MongoDB)** – Handles login, admin dashboard, attendance records, and session management.
- **Machine Learning Client (DeepFace API)** – Processes face detection, verification, and embedding matching.

---

## 👥 Team Members

- [Bill Feng](https://github.com/BillBBle) 
- [Cyan Yan](https://github.com/chenxin-yan) 
- [Leo Wu](https://github.com/leowu777) 
- [Felix Guo](https://github.com/Fel1xgte) 

---

## ⚙️ Setup & Run Instructions

### 1. Clone the Repo

```bash
git clone https://github.com/your-org/containerized-app.git
cd containerized-app
```

### 2. Set up environment variables

Create a `.env` file inside `web-app/` based on the provided example:

```bash
cp web-app/.env.example web-app/.env
```

### 3. Start the App

Using Docker:

```bash
docker-compose up --build
```
This will start:

web-app: Flask server on port 3000
deepface-service: Machine learning API on port 5005
MongoDB: on default port 27017

### 4.Visit the Web UI

Go to: http://localhost:3000