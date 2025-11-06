<<<<<<< HEAD
# AarogyaAI
 – Intelligent Medical Diagnosis & Appointment System

## 📘 Overview

**AarogyaAI
** is an intelligent medical assistance web application designed to help patients analyze potential disease risks (Diabetes, Heart, Liver, Kidney) using **Machine Learning models** and manage doctor appointments seamlessly.
Doctors can log in separately to view, approve, or reject patient appointments.

The system integrates **Flask**, **SQLite**, and **Bootstrap** to provide a secure, scalable, and user-friendly solution for digital healthcare automation.

---

## 🚀 Key Features

### 🧽 Patient Features

* Secure registration and login using JWT authentication.
* Perform disease predictions using trained ML models.
* View AI-generated prediction confidence and recommendations.
* Book appointments directly with a doctor.
* View appointment status (pending, approved, or rejected).
* Dashboard statistics:

  * Total Predictions
  * Total Appointments
  * Healthy Results
  * Risk Detected
  * Last 5 Predictions

### 👨‍⚕️ Doctor Features

* Secure login with JWT-based authentication.
* Dashboard showing:

  * Total Appointments
  * Pending, Approved, Rejected counts
* Approve or reject appointments with reasons.
* View patient details and appointment data.

### 🧠 Machine Learning

* Four trained models for:

  * **Diabetes**
  * **Heart Disease**
  * **Liver Disease**
  * **Kidney Disease**
* Preprocessed with StandardScaler.
* Outputs prediction result and confidence score.

### 🔐 Authentication

* JWT-based secure auth for both roles.
* Role-based redirection (Patient or Doctor).

### 📩 Email Notifications (Optional)

* Automatic confirmation/rejection emails.

---

## 🗂️ Project Structure

```
MediCare-AI/
│
├── backend/
│   ├── app.py
│   ├── database.py
│   ├── email_service.py
│   ├── models/
│   │   ├── diabetes_model.pkl
│   │   ├── heart_model.pkl
│   │   ├── liver_model.pkl
│   │   └── kidney_model.pkl
│   └── medical_app.db
│
├── frontend/
│   ├── index.html
│   ├── patient-login.html
│   ├── doctor-login.html
│   ├── patient-dashboard.html
│   ├── doctor-dashboard.html
│   ├── diabetes.html
│   ├── heart.html
│   ├── liver.html
│   ├── kidney.html
│   └── assets/
│
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation & Setup

### Prerequisites

* Python 3.8+
* pip
* SQLite3

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/mediCare-AI.git
cd mediCare-AI/backend
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt**

```
flask
flask-cors
joblib
bcrypt
pyjwt
```

### Step 3: Run Flask Server

```bash
python app.py
```

Access at [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🧩 Database Schema

### users

| Field     | Type    | Description     |
| --------- | ------- | --------------- |
| id        | INTEGER | Primary key     |
| username  | TEXT    | Unique username |
| email     | TEXT    | Unique email    |
| password  | TEXT    | Hashed password |
| full_name | TEXT    | Patient name    |
| gender    | TEXT    | Gender          |
| phone     | TEXT    | Contact number  |

### doctors

| Field          | Type    | Description            |
| -------------- | ------- | ---------------------- |
| id             | INTEGER | Primary key            |
| username       | TEXT    | Unique doctor username |
| password       | TEXT    | Hashed password        |
| full_name      | TEXT    | Doctor name            |
| specialization | TEXT    | Field of medicine      |

### appointments

| Field            | Type    | Description               |
| ---------------- | ------- | ------------------------- |
| id               | INTEGER | Primary key               |
| user_id          | INTEGER | FK → users.id             |
| doctor_id        | INTEGER | FK → doctors.id           |
| doctor_name      | TEXT    | Doctor name               |
| specialization   | TEXT    | Doctor field              |
| appointment_date | TEXT    | Date                      |
| appointment_time | TEXT    | Time                      |
| status           | TEXT    | pending/approved/rejected |
| reason           | TEXT    | Optional rejection reason |
| notes            | TEXT    | Optional notes            |

### predictions

| Field             | Type     | Description           |
| ----------------- | -------- | --------------------- |
| id                | INTEGER  | Primary key           |
| user_id           | INTEGER  | FK → users.id         |
| disease_type      | TEXT     | Disease type          |
| prediction_result | TEXT     | Positive/Negative     |
| confidence        | REAL     | Prediction confidence |
| prediction_date   | DATETIME | Date of prediction    |
| input_data        | TEXT     | Serialized input      |

---

## 🧠 API Endpoints

### Authentication

| Method | Endpoint             | Description          |
| ------ | -------------------- | -------------------- |
| POST   | `/api/register`      | Register new patient |
| POST   | `/api/login/patient` | Login patient        |
| POST   | `/api/login/doctor`  | Login doctor         |

### Predictions

| Method | Endpoint                 | Description                                       |
| ------ | ------------------------ | ------------------------------------------------- |
| POST   | `/api/predict/<disease>` | Predict diabetes, heart, liver, or kidney disease |

### Appointments

| Method | Endpoint                   | Description               |
| ------ | -------------------------- | ------------------------- |
| POST   | `/api/appointments`        | Book appointment          |
| GET    | `/api/appointments`        | Get patient appointments  |
| GET    | `/api/appointments/doctor` | Get doctor appointments   |
| PUT    | `/api/appointments/<id>`   | Update appointment status |

### Dashboard

| Method | Endpoint                  | Description        |
| ------ | ------------------------- | ------------------ |
| GET    | `/api/stats`              | Patient statistics |
| GET    | `/api/recent-predictions` | Last 5 predictions |

---

## 🧬 Machine Learning Models

* Pre-trained models using Scikit-Learn.
* Each model serialized with `joblib`.
* Scaled with `StandardScaler`.

---

## 🧾 Security

* JWT-based authentication.
* Bcrypt password hashing.
* CORS enabled for frontend access.
* Role-based access control.

---

## 🧰 Technologies Used

| Layer    | Stack                      |
| -------- | -------------------------- |
| Frontend | HTML5, CSS3, JS, Bootstrap |
| Backend  | Flask (Python)             |
| Database | SQLite3                    |
| ML       | Scikit-learn               |
| Auth     | JWT                        |

---

## 📈 Future Enhancements

* Disease history analytics.
* Admin dashboard.
* PDF report generation.
* Chatbot integration.

---

## 👨‍💻 Author

**Ramesh Siravati**
B.Tech Student  
📧  mailto:rameshsiravati2004.com
🔗  https://linkedin.com/in/rameshsiravati

---

 
=======
# AarogyaAI
>>>>>>> origin/main
