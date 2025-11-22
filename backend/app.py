# backend/app.py
import os
import joblib
import traceback
from datetime import datetime, timedelta
from functools import wraps
import bcrypt
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import jwt

from database import Database
from email_service import EmailService


# =====================================================
# CONFIGURATION
# =====================================================
JWT_SECRET = os.environ.get('JWT_SECRET', 'replace-this-secret-with-env-var')
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_HOURS = int(os.environ.get('JWT_EXP_DELTA_HOURS', 24))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, '../frontend')
MODELS_DIR = os.path.join(BASE_DIR, 'models')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)

 
db = Database()
email_service = EmailService()

# =====================================================
# LOAD MACHINE LEARNING MODELS
# =====================================================
models = {}
def load_models():
    global models
    for disease in ['diabetes', 'heart', 'liver', 'kidney']:
        path = os.path.join(MODELS_DIR, f'{disease}_model.pkl')
        if os.path.exists(path):
            obj = joblib.load(path)
            
            if hasattr(obj, 'predict'):
                models[disease] = {'model': obj, 'scaler': None, 'feature_columns': None}
            elif isinstance(obj, dict):
                 
                models[disease] = {
                    'model': obj.get('model') or obj.get('estimator') or obj.get('clf'),
                    'scaler': obj.get('scaler'),
                    'feature_columns': obj.get('feature_columns') or obj.get('features') or obj.get('columns')
                }
            else:
                app.logger.warning(f"Unsupported model file format for {disease}")
                continue
            app.logger.info(f"✅ Loaded model: {disease}")
        else:
            app.logger.warning(f"⚠️ Model not found for: {disease}")

load_models()

# =====================================================
# JWT HELPERS
# =====================================================
def generate_token(user_id, username, role='patient', expires_hours=JWT_EXP_DELTA_HOURS):
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=expires_hours),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token   

def verify_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return {'error': 'Token expired'}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token'}

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth:
            return jsonify({'error': 'Authorization header missing'}), 401

        parts = auth.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'error': 'Invalid token format'}), 401

        token = parts[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

         
        request.user_id = payload.get('user_id')
        request.username = payload.get('username')
        request.role = payload.get('role', 'patient')
        request.doctor_id = payload.get('doctor_id')

         
        return f(*args, **kwargs)
    return decorated



# =====================================================
# AUTHENTICATION ROUTES
# =====================================================
@app.route('/api/register', methods=['POST'])
def register_patient():
    try:
        data = request.json or {}
        for field in ['username', 'email', 'password', 'full_name']:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400

        user_id = db.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            full_name=data['full_name'],
            phone=data.get('phone'),
            gender=data.get('gender')
        )
        if not user_id:
            return jsonify({'error': 'Username or email already exists'}), 400

        return jsonify({'success': True, 'message': 'Registration successful'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

 
@app.route('/api/login', methods=['POST'])
@app.route('/api/login/patient', methods=['POST'])
def login_patient():
    try:
        data = request.json or {}
        user = db.verify_user(data.get('username'), data.get('password'))
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        token = generate_token(user['id'], user['username'], 'patient')
        return jsonify({'success': True, 'token': token, 'user': user})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/login/doctor', methods=['POST'])
def doctor_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    doctor = db.verify_doctor(username, password)
    if not doctor:
        return jsonify({"success": False, "error": "Invalid credentials"}), 401

    payload = {
        "doctor_id": doctor['id'],
        "username": doctor['username'],
        "role": "doctor",
        "exp": datetime.utcnow() + timedelta(hours=12)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return jsonify({"success": True, "token": token, "doctor": doctor})


# =====================================================
# PROFILE & HISTORY ROUTES
# =====================================================
@app.route('/api/profile', methods=['GET'])
@token_required
def get_profile():
    try:
        if request.role == 'doctor':
            doctor = db.get_doctor_by_username(request.username)
            return jsonify({'success': True, 'profile': doctor})
        else:
            patient = db.get_user_by_id(request.user_id)
            return jsonify({'success': True, 'profile': patient})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history', methods=['GET'])
@token_required
def get_history():
    try:
        if request.role == 'patient':
            preds = db.get_user_predictions(request.user_id)
            return jsonify({'success': True, 'predictions': preds})

        elif request.role == 'doctor':
            appointments = db.get_doctor_appointments(doctor_id=request.user_id)
            return jsonify({'success': True, 'appointments': appointments})

        return jsonify({'error': 'Invalid role'}), 403
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

 
# =====================================================
# DASHBOARD STATS + RECENT PREDICTIONS (FIXED)
# =====================================================
@app.route('/api/stats', methods=['GET'])
@token_required
def get_stats():
    try:
        if request.role == 'patient':
             
            predictions = db.get_user_predictions(request.user_id)

            total_predictions = len(predictions)
            healthy_results = sum(1 for p in predictions if p['prediction_result'] == 'Negative')
            risk_detected = sum(1 for p in predictions if p['prediction_result'] == 'Positive')

            
            user_appointments = db.get_user_appointments(request.user_id)
            total_appointments = len(user_appointments)

            return jsonify({
                'success': True,
                'total_predictions': total_predictions,
                'healthy_results': healthy_results,
                'risk_detected': risk_detected,
                'total_appointments': total_appointments
            })

        elif request.role == 'doctor':
            stats = db.get_appointment_statistics(doctor_id=request.user_id)
            return jsonify({'success': True, 'stats': stats})

        else:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    except Exception as e:
        print("🔥 Error in /api/stats:", e)
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/recent-predictions', methods=['GET'])
@token_required
def get_recent_predictions():
    try:
        if request.role != 'patient':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403

        preds = db.get_user_predictions(request.user_id) or []
         
        preds = sorted(preds, key=lambda x: x['prediction_date'], reverse=True)[:5]

        return jsonify({'success': True, 'predictions': preds})

    except Exception as e:
        print("🔥 Error in /api/recent-predictions:", e)
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
# =====================================================
# RECENT PREDICTIONS 
# =====================================================
@app.route('/api/stats', methods=['GET'],endpoint='stats')
@token_required
def get_stats():
    try:
        if request.role == 'patient':
             
            predictions = db.get_user_predictions(request.user_id)

            total_predictions = len(predictions)
            healthy_results = sum(1 for p in predictions if p['prediction_result'] == 'Negative')
            risk_detected = sum(1 for p in predictions if p['prediction_result'] == 'Positive')

             
            user_appointments = db.get_user_appointments(request.user_id)
            total_appointments = len(user_appointments)

            return jsonify({
                'success': True,
                'total_predictions': total_predictions,
                'healthy_results': healthy_results,
                'risk_detected': risk_detected,
                'total_appointments': total_appointments
            })

        elif request.role == 'doctor':
            stats = db.get_appointment_statistics(doctor_id=request.user_id)
            return jsonify({'success': True, 'stats': stats})

        else:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    except Exception as e:
        print("🔥 Error in /api/stats:", e)
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/recent-predictions', methods=['GET'], endpoint='recent_predictions')
@token_required
def get_recent_predictions():
    try:
        if request.role != 'patient':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403

        preds = db.get_user_predictions(request.user_id) or []
         
        preds = sorted(preds, key=lambda x: x['prediction_date'], reverse=True)[:5]

        return jsonify({'success': True, 'predictions': preds})

    except Exception as e:
        print("🔥 Error in /api/recent-predictions:", e)
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500




 
@app.route('/api/appointments/<int:appointment_id>', methods=['PUT'])
@token_required
def update_appointment_status(current_user, appointment_id):
    try:
        if current_user['role'] != 'doctor':
            return jsonify({"success": False, "error": "Unauthorized"}), 403

        data = request.get_json()
        status = data.get('status')
        reason = data.get('reason', None)

         
        apt_details = db.update_appointment_status(
            appointment_id, status, current_user['doctor_id'], reason
        )

        if not apt_details:
            return jsonify({"success": False, "error": "Appointment not found"}), 404

         
        email_service = EmailService()
        patient_email, patient_name, date, time, doctor_name, specialization = apt_details

        if status == 'approved':
            email_service.send_appointment_confirmation(
                patient_email, patient_name, doctor_name, date, time, specialization
            )
        elif status == 'rejected':
            email_service.send_appointment_rejection(
                patient_email, patient_name, doctor_name, date, time, reason
            )

        return jsonify({"success": True, "message": f"Appointment {status} successfully"})

    except Exception as e:
        print("Error updating appointment:", e)
        return jsonify({"success": False, "error": str(e)}), 500

# =====================================================
# PREDICTION ROUTES 
# =====================================================
@app.route('/api/predict/<disease>', methods=['POST'])
@token_required
def predict_disease(disease):
    try:
        disease = disease.lower()
        if disease not in models:
            return jsonify({'error': f'{disease} model not available'}), 400

        model_info = models[disease]
        model = model_info.get('model')
        scaler = model_info.get('scaler')
        features = model_info.get('feature_columns')
        data = request.json or {}

         
        normalized = {}
        for key, val in data.items():
            if isinstance(val, str):
                v = val.strip().lower()
                if v in ['male', 'm']: normalized[key] = 1
                elif v in ['female', 'f']: normalized[key] = 0
                elif v in ['yes', 'y', 'true', 'positive']: normalized[key] = 1
                elif v in ['no', 'n', 'false', 'negative']: normalized[key] = 0
                else:
                    try: normalized[key] = float(v)
                    except: normalized[key] = v
            else:
                normalized[key] = val

        if not features:
            features = sorted(normalized.keys())

        missing = [f for f in features if f not in normalized]
        if missing:
            return jsonify({'error': f'Missing input fields: {", ".join(missing)}'}), 400

         
        try:
            X = [[float(normalized[f]) for f in features]]
        except Exception as ve:
            return jsonify({'error': f'Invalid numeric input: {ve}'}), 400

        if scaler:
            try:
                X = scaler.transform(X)
            except Exception as e:
                app.logger.warning(f"Scaler transform failed for {disease}: {e}")

        prediction = int(model.predict(X)[0])
        confidence = float(max(model.predict_proba(X)[0])) if hasattr(model, 'predict_proba') else 1.0
        result = 'Positive' if prediction == 1 else 'Negative'

        prediction_id = db.save_prediction(
            user_id=request.user_id,
            disease_type=disease.capitalize(),
            prediction_result=result,
            confidence=confidence,
            input_data=data
        )

        return jsonify({
            'success': True,
            'prediction_id': prediction_id,
            'result': result,
            'confidence': round(confidence, 3),
            'recommendations': get_recommendations(disease, prediction)
        })
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({'error': f'Server error: {str(e)}'}), 500

0
# =====================================================
# RECOMMENDATION LOGIC
# =====================================================
def get_recommendations(disease, prediction):
    if disease == 'diabetes':
        return ['Consult an endocrinologist or diabetologist immediately',
            'Get HbA1c and fasting blood sugar tests done',
            'Monitor blood glucose levels regularly',
            'Follow a balanced diet with controlled carbohydrates',
            'Regular physical activity (30 minutes daily)',
            'Maintain healthy body weight',
            'Stay hydrated and avoid sugary drinks'] if prediction else ['Maintain a healthy lifestyle to prevent diabetes',
            'Regular health checkups annually',
            'Balanced diet with plenty of vegetables and fruits',
            'Regular exercise (at least 150 minutes per week)',
            'Maintain healthy body weight',
            'Limit sugar and processed food intake']
    if disease == 'heart':
        return ['Consult a cardiologist urgently',
            'Get ECG, Echo, and cardiac enzyme tests',
            'Monitor blood pressure daily',
            'Take prescribed medications regularly',
            'Reduce salt and fatty food intake',
            'Quit smoking and limit alcohol',
            'Manage stress through relaxation techniques',
            'Regular moderate exercise as advised by doctor'] if prediction else ['Maintain heart-healthy lifestyle',
            'Regular cardiovascular checkups',
            'Balanced diet rich in omega-3 fatty acids',
            'Regular aerobic exercise',
            'Maintain healthy blood pressure and cholesterol',
            'Avoid smoking and excessive alcohol',
            'Manage stress effectively']
    if disease == 'liver':
        return ['Consult a hepatologist or gastroenterologist',
            'Get liver function tests (LFT) done',
            'Ultrasound or CT scan of liver may be required',
            'Avoid alcohol completely',
            'Maintain healthy diet with limited fats',
            'Stay hydrated',
            'Avoid unnecessary medications',
            'Get vaccinated for Hepatitis A and B'] if prediction else ['Maintain liver health through healthy lifestyle',
            'Limit alcohol consumption',
            'Balanced diet with adequate protein',
            'Regular exercise',
            'Avoid unnecessary medications',
            'Stay hydrated',
            'Get vaccinated for Hepatitis if not done']
    if disease == 'kidney':
        return ['Consult a nephrologist immediately',
            'Get kidney function tests (creatinine, BUN, GFR)',
            'Ultrasound of kidneys may be required',
            'Monitor blood pressure regularly',
            'Control diabetes if present',
            'Limit salt and protein intake as advised',
            'Stay well hydrated',
            'Avoid NSAIDs and nephrotoxic drugs'] if prediction else ['Maintain kidney health through healthy habits',
            'Drink adequate water daily (8-10 glasses)',
            'Regular exercise',
            'Maintain healthy blood pressure',
            'Control blood sugar if diabetic',
            'Limit salt intake',
            'Avoid excessive protein supplements']
    return []

# =====================================================
# APPOINTMENT ROUTES
# =====================================================
@app.route('/api/appointments', methods=['POST'])
@token_required
def book_appointment():
    if request.role != 'patient':
        return jsonify({'error': 'Only patients can book appointments'}), 403

    try:
        data = request.json or {}
        required = ['doctor_name', 'specialization', 'appointment_date', 'appointment_time']
        for f in required:
            if f not in data:
                return jsonify({'error': f'Missing field: {f}'}), 400
         
        existing = db.check_slot(
            doctor_name=data['doctor_name'],
            appointment_date=data['appointment_date'],
            appointment_time=data['appointment_time']
            )

        if existing:
            return jsonify({
                'success': False,
                'error': 'This time slot is already booked. Please choose another time.'
                }), 400
 

        apt_id = db.save_appointment(
            user_id=request.user_id,
            prediction_id=data.get('prediction_id'),
            doctor_name=data['doctor_name'],
            specialization=data['specialization'],
            appointment_date=data['appointment_date'],
            appointment_time=data['appointment_time'],
            notes=data.get('notes')
        )

         
        if hasattr(email_service, 'send_appointment_booking_notification'):
            patient = db.get_user_by_id(request.user_id)
            email_service.send_appointment_booking_notification(
                patient_email=patient['email'],
                patient_name=patient['full_name'],
                doctor_name=data['doctor_name'],
                appointment_date=data['appointment_date'],
                appointment_time=data['appointment_time']
            )

        return jsonify({'success': True, 'message': 'Appointment booked successfully', 'appointment_id': apt_id})

    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/appointments', methods=['GET'])
@token_required
def get_appointments():
    try:
        if request.role == 'patient':
            appointments = db.get_user_appointments(request.user_id)
        elif request.role == 'doctor':
            appointments = db.get_doctor_appointments(request.doctor_id)
        else:
            return jsonify({'error': 'Invalid role'}), 403

        return jsonify({'success': True, 'appointments': appointments})
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


 
@app.route('/api/appointments/doctor', methods=['GET'])
@token_required
def get_doctor_appointments():
    if request.role != 'doctor':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    appointments = db.get_doctor_appointments(request.doctor_id)
    return jsonify({'success': True, 'appointments': appointments})


# =====================================================
# DOCTOR APPROVAL SYSTEM (Final Fixed Version)
# =====================================================

@app.route('/api/doctor/appointments/<int:appointment_id>/approve', methods=['POST'])
@token_required
def approve_appointment(appointment_id):
    try:
        if request.role != 'doctor':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403

        data = request.get_json() or {}
        reason = data.get('reason', '')
        doctor_id = request.doctor_id   

         
        details = db.update_appointment_status(appointment_id, 'approved', doctor_id, reason)
        if not details:
            return jsonify({'success': False, 'error': 'Appointment not found'}), 404

         
        if hasattr(email_service, 'send_appointment_confirmation'):
            patient_email, patient_name, date, time, doctor_name, specialization = details
            email_service.send_appointment_confirmation(
                patient_email, patient_name, doctor_name, date, time, specialization
            )

        return jsonify({'success': True, 'message': 'Appointment approved successfully'})

    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/doctor/appointments/<int:appointment_id>/reject', methods=['POST'])
@token_required
def reject_appointment(appointment_id):
    try:
        if request.role != 'doctor':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403

        data = request.get_json() or {}
        reason = data.get('reason', 'Not specified')
        doctor_id = request.doctor_id

         
        details = db.update_appointment_status(appointment_id, 'rejected', doctor_id, reason)
        if not details:
            return jsonify({'success': False, 'error': 'Appointment not found'}), 404

         
        if hasattr(email_service, 'send_appointment_rejection'):
            patient_email, patient_name, date, time, doctor_name, specialization = details
            email_service.send_appointment_rejection(
                patient_email, patient_name, doctor_name, date, time, reason
            )

        return jsonify({'success': True, 'message': 'Appointment rejected successfully'})

    except Exception as e:
        app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

# =====================================================
# PUBLIC ROUTES
# =====================================================
@app.route('/api/doctors', methods=['GET'])
def get_doctors():
    doctors = db.get_all_doctors()
    return jsonify({'success': True, 'doctors': doctors})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'models_loaded': list(models.keys()), 'time': datetime.utcnow().isoformat()})

 
 
 
@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

 
@app.route('/dashboard.html')
def redirect_dashboard():
    return send_from_directory(FRONTEND_DIR, 'patient-dashboard.html')

  
# MAIN
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))