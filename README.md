![Lint-free](https://github.com/nyu-software-engineering/containerized-app-exercise/actions/workflows/lint.yml/badge.svg)
![Web-App Tests](https://github.com/nyu-software-engineering/containerized-app-exercise/actions/workflows/CI.yml/badge.svg?branch=main&job=test&matrix=subdir:web-app)
![Web-App Build](https://github.com/nyu-software-engineering/containerized-app-exercise/actions/workflows/CI.yml/badge.svg?branch=main&job=build&matrix=service:web-app)
![ML-Client Tests](https://github.com/nyu-software-engineering/containerized-app-exercise/actions/workflows/CI.yml/badge.svg?branch=main&job=test&matrix=subdir:machine-learning-client)
![Deepface Build](https://github.com/nyu-software-engineering/containerized-app-exercise/actions/workflows/CI.yml/badge.svg?branch=main&job=build&matrix=service:deepface)

# SmartGate 🚪📷

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

Run the `setup-env.sh` script and modify `.env` files as needed

```bash
chmod +x ./setup-env.sh
./setup-env.sh
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

Go to: <http://localhost:3000>
