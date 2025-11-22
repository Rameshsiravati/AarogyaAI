import sqlite3
from datetime import datetime
import bcrypt

class Database:
    def __init__(self, db_name='medical_app.db'):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_database(self):
        """Initialize all database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Patients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password BLOB NOT NULL,
                full_name TEXT NOT NULL,
                phone TEXT,
                date_of_birth DATE,
                gender TEXT,
                role TEXT DEFAULT 'patient',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Doctors table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password BLOB NOT NULL,
                full_name TEXT NOT NULL,
                phone TEXT,
                specialization TEXT NOT NULL,
                qualification TEXT,
                experience_years INTEGER,
                role TEXT DEFAULT 'doctor',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                disease_type TEXT NOT NULL,
                prediction_result TEXT NOT NULL,
                confidence REAL,
                input_data TEXT,
                prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Appointments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                prediction_id INTEGER,
                doctor_id INTEGER,
                doctor_name TEXT NOT NULL,
                specialization TEXT NOT NULL,
                appointment_date DATE NOT NULL,
                appointment_time TIME NOT NULL,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                doctor_notes TEXT,
                approved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (doctor_id) REFERENCES doctors (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
         
        self.insert_sample_doctors()
    
    # ---------------- DOCTOR SETUP ----------------
    def insert_sample_doctors(self):
        """Insert sample doctors if DB is empty"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM doctors')
        if cursor.fetchone()[0] == 0:
            password = bcrypt.hashpw("doctor123".encode('utf-8'), bcrypt.gensalt())
            
            doctors = [
                ('dr.sarah', 'dr.sarah@hospital.com', password, 'Dr. Sarah Johnson', 
                 '555-0101', 'Diabetologist', 'MD, Endocrinology', 10),
                ('dr.michael', 'dr.michael@hospital.com', password, 'Dr. Michael Chen', 
                 '555-0102', 'Cardiologist', 'MD, Cardiology', 15),
                ('dr.emily', 'dr.emily@hospital.com', password, 'Dr. Emily Davis', 
                 '555-0103', 'Hepatologist', 'MD, Gastroenterology', 12),
                ('dr.robert', 'dr.robert@hospital.com', password, 'Dr. Robert Williams', 
                 '555-0104', 'Nephrologist', 'MD, Nephrology', 8)
            ]
            
            cursor.executemany('''
                INSERT INTO doctors (username, email, password, full_name, phone, 
                                   specialization, qualification, experience_years)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', doctors)
            
            conn.commit()
        
        conn.close()
    
    # ---------------- PATIENT AUTH ----------------
    def create_user(self, username, email, password, full_name, phone=None, dob=None, gender=None):
        """Create a new patient"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password, full_name, phone, date_of_birth, gender, role)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'patient')
            ''', (username, email, hashed_password, full_name, phone, dob, gender))
            
            user_id = cursor.lastrowid
            conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()

    def verify_user(self, username, password):
        """Verify a patient during login"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, email, password, full_name FROM users WHERE username=?", (username,))
        user = cur.fetchone()
        conn.close()

        if user:
            stored_hash = user[3]
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode('utf-8')

            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'full_name': user[4],
                    'role': 'patient'
                }
        return None

    def get_user_by_id(self, user_id):
        """Fetch patient details by ID (used for booking and emails)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, email, full_name, phone, date_of_birth, gender
            FROM users WHERE id = ?
        ''', (user_id,))
        user = cursor.fetchone()
        conn.close()
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'full_name': user[3],
                'phone': user[4],
                'date_of_birth': user[5],
                'gender': user[6],
                'role': 'patient'
            }
        return None

    # ---------------- DOCTOR AUTH ----------------
    def verify_doctor(self, username, password):
        """Verify doctor login"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, username, email, password, full_name, phone, specialization
            FROM doctors WHERE username=?
        """, (username,))
        doctor = cur.fetchone()
        conn.close()

        print(f"🧠 Checking doctor {username}: {doctor}")   

        if doctor:
            stored_hash = doctor[3]
            print(f"Stored hash: {stored_hash}")   

            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode('utf-8')

            print(f"CheckPW: {bcrypt.checkpw(password.encode('utf-8'), stored_hash)}")   

            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                return {
                    'id': doctor[0],
                    'username': doctor[1],
                    'email': doctor[2],
                    'full_name': doctor[4],
                    'phone': doctor[5],
                    'specialization': doctor[6],
                    'role': 'doctor'
                }
        return None


  
    def get_doctor_by_username(self, username):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, username, email, full_name, phone, specialization, role
            FROM doctors WHERE username=?
        """, (username,))
        row = cur.fetchone()
        conn.close()
        if not row: return None
        return {
            'id': row[0], 'username': row[1], 'email': row[2],
            'full_name': row[3], 'phone': row[4],
            'specialization': row[5], 'role': row[6] or 'doctor'
        }


    def get_all_doctors(self):
        """List of all doctors"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, full_name, specialization, qualification, experience_years
            FROM doctors
            ORDER BY full_name
        ''')
        doctors = cursor.fetchall()
        conn.close()
        
        return [{
            'id': d[0],
            'full_name': d[1],
            'specialization': d[2],
            'qualification': d[3],
            'experience_years': d[4]
        } for d in doctors]

    # ---------------- PREDICTIONS ----------------
    def save_prediction(self, user_id, disease_type, prediction_result, confidence, input_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO predictions (user_id, disease_type, prediction_result, confidence, input_data)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, disease_type, prediction_result, confidence, str(input_data)))
        prediction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return prediction_id
    
    def get_user_predictions(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, disease_type, prediction_result, confidence, prediction_date
            FROM predictions
            WHERE user_id = ?
            ORDER BY prediction_date DESC
        ''', (user_id,))
        predictions = cursor.fetchall()
        conn.close()
        return [{
            'id': p[0],
            'disease_type': p[1],
            'prediction_result': p[2],
            'confidence': p[3],
            'prediction_date': p[4]
        } for p in predictions]

    # ---------------- APPOINTMENTS ----------------
    def save_appointment(self, user_id, prediction_id, doctor_name, specialization, appointment_date, appointment_time, notes=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM doctors WHERE full_name = ?', (doctor_name,))
        doctor = cursor.fetchone()
        doctor_id = doctor[0] if doctor else None
        
        cursor.execute('''
            INSERT INTO appointments (user_id, prediction_id, doctor_id, doctor_name, specialization, appointment_date, appointment_time, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (user_id, prediction_id, doctor_id, doctor_name, specialization, appointment_date, appointment_time, notes))
        appointment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return appointment_id
    
    def get_user_appointments(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, doctor_name, specialization, appointment_date, appointment_time, status, notes, doctor_notes, created_at
            FROM appointments
            WHERE user_id = ?
            ORDER BY appointment_date DESC, appointment_time DESC
        ''', (user_id,))
        appointments = cursor.fetchall()
        conn.close()
        return [{
            'id': a[0],
            'doctor_name': a[1],
            'specialization': a[2],
            'appointment_date': a[3],
            'appointment_time': a[4],
            'status': a[5],
            'notes': a[6],
            'doctor_notes': a[7],
            'created_at': a[8]
        } for a in appointments]

    def get_doctor_appointments(self, doctor_id=None, status=None):
        """Return doctor’s appointments list"""
        conn = self.get_connection()
        cursor = conn.cursor()
        query = '''
            SELECT a.id, u.full_name, u.email, u.phone, u.gender,
                   a.doctor_name, a.specialization, a.appointment_date, a.appointment_time,
                   a.status, a.notes, a.created_at,
                   p.disease_type, p.prediction_result, p.confidence
            FROM appointments a
            JOIN users u ON a.user_id = u.id
            LEFT JOIN predictions p ON a.prediction_id = p.id
        '''
        conditions = []
        params = []
        if doctor_id:
            conditions.append('a.doctor_id = ?')
            params.append(doctor_id)
        if status:
            conditions.append('a.status = ?')
            params.append(status)
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY a.appointment_date DESC, a.appointment_time DESC'
        cursor.execute(query, params)
        appointments = cursor.fetchall()
        conn.close()
        return [{
            'id': apt[0],
            'patient_name': apt[1],
            'patient_email': apt[2],
            'patient_phone': apt[3],
            'patient_gender': apt[4],
            'doctor_name': apt[5],
            'specialization': apt[6],
            'appointment_date': apt[7],
            'appointment_time': apt[8],
            'status': apt[9],
            'notes': apt[10],
            'created_at': apt[11],
            'disease_type': apt[12],
            'prediction_result': apt[13],
            'confidence': apt[14]
        } for apt in appointments]

    def get_doctor_appointments_by_username(self, username):
        """Return all appointments where this doctor’s username matches"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT a.*, d.username FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            WHERE d.username = ?
        """, (username,))
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    def check_slot(self, doctor_name, appointment_date, appointment_time):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id FROM appointments
            WHERE doctor_name = ?
            AND appointment_date = ?
            AND appointment_time = ?
            AND status IN ('pending', 'approved')
        """, (doctor_name, appointment_date, appointment_time))

        result = cursor.fetchone()
        conn.close()

        return result is not None


    def update_appointment_status(self, appointment_id, status, doctor_id=None, reason=None):
        conn = self.get_connection()
        cur = conn.cursor()

         
        cur.execute("""
            UPDATE appointments
            SET status = ?, reason = ?, doctor_id = ?
            WHERE id = ?
        """, (status, reason, doctor_id, appointment_id))
        conn.commit()

         
        cur.execute("""
            SELECT u.email AS patient_email,
                u.full_name AS patient_name,
                a.appointment_date,
                a.appointment_time,
                a.doctor_name,
                a.specialization
            FROM appointments a
            JOIN users u ON a.user_id = u.id
            WHERE a.id = ?
        """, (appointment_id,))
        
        details = cur.fetchone()
        conn.close()
        return details



    def get_appointment_statistics(self, doctor_id=None):
        """Return summary stats for a doctor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        where_clause = 'WHERE doctor_id = ?' if doctor_id else ''
        params = [doctor_id] if doctor_id else []
        
        cursor.execute(f'SELECT COUNT(*) FROM appointments {where_clause}', params)
        total = cursor.fetchone()[0]
        cursor.execute(f'SELECT COUNT(*) FROM appointments {where_clause} {"AND" if doctor_id else "WHERE"} status = "pending"', params)
        pending = cursor.fetchone()[0]
        cursor.execute(f'SELECT COUNT(*) FROM appointments {where_clause} {"AND" if doctor_id else "WHERE"} status = "approved"', params)
        approved = cursor.fetchone()[0]
        cursor.execute(f'SELECT COUNT(*) FROM appointments {where_clause} {"AND" if doctor_id else "WHERE"} status = "rejected"', params)
        rejected = cursor.fetchone()[0]
        conn.close()
        
        return {
            'total': total,
            'pending': pending,
            'approved': approved,
            'rejected': rejected
        }
     
