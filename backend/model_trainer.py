import os
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score

class MultiDiseasePredictor:
    def __init__(self):
        self.models = {}
        self.label_encoders = {}

    # ---------------------- DIABETES MODEL ----------------------
    def train_diabetes_model(self):
        print("\n🔧 Training Diabetes Model...")
        try:
            df = pd.read_csv('datasets/diabetes.csv')
            feature_columns = [
                'Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness',
                'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age'
            ]
            target_column = 'Outcome'

            X = df[feature_columns].fillna(df[feature_columns].mean())
            y = df[target_column]

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42)

            scaler = StandardScaler()
            X_train = scaler.fit_transform(X_train)
            X_test = scaler.transform(X_test)

            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)

            acc = accuracy_score(y_test, model.predict(X_test))
            print(f"✅ Diabetes Accuracy: {acc * 100:.2f}%")

            self.models['diabetes'] = {
                'model': model,
                'scaler': scaler,
                'features': feature_columns
            }
            return True
        except Exception as e:
            print("❌ Diabetes Model Failed:", e)
            return False

    # ---------------------- HEART MODEL ----------------------
    def train_heart_model(self):
        print("\n🔧 Training Heart Disease Model...")
        try:
            df = pd.read_csv('datasets/heart.csv')
            feature_columns = [
                'age', 'sex', 'cp', 'trtbps', 'chol', 'fbs', 'restecg',
                'thalachh', 'exng', 'oldpeak', 'slp', 'caa', 'thall'
            ]
            target_column = 'output'

            X = df[feature_columns].fillna(df[feature_columns].mean())
            y = df[target_column]

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42)

            scaler = StandardScaler()
            X_train = scaler.fit_transform(X_train)
            X_test = scaler.transform(X_test)

            model = GradientBoostingClassifier(n_estimators=120, random_state=42)
            model.fit(X_train, y_train)

            acc = accuracy_score(y_test, model.predict(X_test))
            print(f"✅ Heart Model Accuracy: {acc * 100:.2f}%")

            self.models['heart'] = {
                'model': model,
                'scaler': scaler,
                'features': feature_columns
            }
            return True
        except Exception as e:
            print("❌ Heart Model Failed:", e)
            return False

    # ---------------------- LIVER MODEL ----------------------
    def train_liver_model(self):
        print("\n🔧 Training Liver Disease Model...")
        try:
            df = pd.read_csv('datasets/liver.csv')
            feature_columns = [
                'Age', 'Gender', 'Total_Bilirubin', 'Direct_Bilirubin',
                'Alkaline_Phosphotase', 'Alamine_Aminotransferase',
                'Aspartate_Aminotransferase', 'Total_Protiens', 'Albumin',
                'Albumin_and_Globulin_Ratio'
            ]
            target_column = 'Dataset'

            X = df[feature_columns].copy()
            y = df[target_column]

            if 'Gender' in X.columns:
                enc = LabelEncoder()
                X['Gender'] = enc.fit_transform(X['Gender'])
                self.label_encoders['liver_gender'] = enc

            X = X.fillna(X.mean())

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42)

            scaler = StandardScaler()
            X_train = scaler.fit_transform(X_train)
            X_test = scaler.transform(X_test)

            model = RandomForestClassifier(n_estimators=120, random_state=42)
            model.fit(X_train, y_train)

            acc = accuracy_score(y_test, model.predict(X_test))
            print(f"✅ Liver Model Accuracy: {acc * 100:.2f}%")

            self.models['liver'] = {
                'model': model,
                'scaler': scaler,
                'features': feature_columns
            }
            return True
        except Exception as e:
            print("❌ Liver Model Failed:", e)
            return False

    # ---------------------- KIDNEY MODEL ----------------------
    def train_kidney_model(self):
        print("\n🔧 Training Kidney Disease Model...")
        try:
            df = pd.read_csv('datasets/kidney.csv')
            feature_columns = [
                'age', 'bp', 'sg', 'al', 'su', 'bgr', 'bu', 'sc',
                'sod', 'pot', 'hemo', 'pcv', 'wc', 'rc'
            ]
            target_column = 'classification'

            X = df[feature_columns].copy()
            y = df[target_column]

            for col in X.columns:
                if X[col].dtype == 'object':
                    enc = LabelEncoder()
                    X[col] = enc.fit_transform(X[col].astype(str))
                    self.label_encoders[f'kidney_{col}'] = enc

            if y.dtype == 'object':
                enc_t = LabelEncoder()
                y = enc_t.fit_transform(y)
                self.label_encoders['kidney_target'] = enc_t

            X = X.fillna(X.mean())

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42)

            scaler = StandardScaler()
            X_train = scaler.fit_transform(X_train)
            X_test = scaler.transform(X_test)

            model = RandomForestClassifier(n_estimators=120, random_state=42)
            model.fit(X_train, y_train)

            acc = accuracy_score(y_test, model.predict(X_test))
            print(f"✅ Kidney Model Accuracy: {acc * 100:.2f}%")

            self.models['kidney'] = {
                'model': model,
                'scaler': scaler,
                'features': feature_columns
            }
            return True
        except Exception as e:
            print("❌ Kidney Model Failed:", e)
            return False

     
    def save_models(self):
        os.makedirs("models", exist_ok=True)
        for name, model_data in self.models.items():
            joblib.dump(model_data, f"models/{name}_model.pkl")
            print(f"📌 Saved {name} model")

        if self.label_encoders:
            joblib.dump(self.label_encoders, "models/label_encoders.pkl")
            print("📌 Saved label encoders")

def main():
    trainer = MultiDiseasePredictor()
    results = {
        "Diabetes": trainer.train_diabetes_model(),
        "Heart": trainer.train_heart_model(),
        "Liver": trainer.train_liver_model(),
        "Kidney": trainer.train_kidney_model(),
    }

    trainer.save_models()

    print("\n================ TRAINING SUMMARY ================")
    for disease, status in results.items():
        print(f"{disease}: {'✅ SUCCESS' if status else '❌ FAILED'}")

    print("\n✅ ALL DONE! Models saved in /models directory.\n")

if __name__ == "__main__":
    main()