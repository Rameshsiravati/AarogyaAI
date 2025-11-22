import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

class EmailService:
    def __init__(self):
         
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port_tls = 587   # STARTTLS
        self.smtp_port_ssl = 465   # SSL fallback

         
        self.sender_email = os.getenv("MAIL_SENDER", "siravatiramesh@gmail.com")
        self.sender_password = os.getenv("MAIL_APP_PASSWORD", "vhlk wyum rpzi vjmn")  # Gmail App Password

         
        self.hospital_name = os.getenv("HOSPITAL_NAME", "MediCare AI Hospital")
        self.hospital_phone = os.getenv("HOSPITAL_PHONE", "+1 (555) 123-4567")
        self.hospital_address = os.getenv("HOSPITAL_ADDRESS", "123 Health Street, Medical City")
        self.reply_to = os.getenv("MAIL_REPLY_TO", self.sender_email)

    # ---------------------------- Internal helpers ----------------------------

    def _footer_html(self) -> str:
        return f"""
            <div style="text-align:center;color:#7f8c8d;font-size:13px;margin-top:20px;line-height:1.4">
                <div>{self.hospital_name} • {self.hospital_phone}</div>
                <div>{self.hospital_address}</div>
            </div>
        """

    def _frame_html(self, title: str, header_color: str, inner_html: str) -> str:
        """Wraps provided HTML in a consistent branded template."""
        return f"""
        <html>
        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
        </head>
        <body style="margin:0;padding:0;background:#f6f8fb;font-family:Arial,Helvetica,sans-serif;">
            <div style="max-width:640px;margin:0 auto;padding:16px;">
                <div style="background:{header_color};color:#fff;padding:18px 20px;border-radius:12px 12px 0 0;text-align:center;">
                    <div style="font-size:20px;font-weight:700;margin:0;">{title}</div>
                </div>
                <div style="background:#ffffff;padding:20px;border-radius:0 0 12px 12px;border:1px solid #eaecef;border-top:none;">
                    {inner_html}
                    {self._footer_html()}
                </div>
            </div>
        </body>
        </html>
        """

    def _send(self, to_email: str, subject: str, html_body: str) -> bool:
        """Send HTML email safely, with TLS and SSL fallback."""
        try:
            if not self.sender_email or not self.sender_password:
                print(f"⚠️ Email not configured. Skipping send to {to_email}.")
                return True  

             
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = formataddr((self.hospital_name, self.sender_email))
            msg["To"] = to_email
            msg.add_header("Reply-To", self.reply_to)

            plain_fallback = (
                "This email contains rich formatting. "
                "Please view it in an HTML-capable email client."
            )
            msg.attach(MIMEText(plain_fallback, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            
            try:
                with smtplib.SMTP(self.smtp_server, self.smtp_port_tls, timeout=20) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(self.sender_email, self.sender_password)
                    server.send_message(msg)
                print(f"✅ Email sent (TLS) to {to_email}")
                return True
            except Exception as e_tls:
                print(f"ℹ️ TLS send failed ({e_tls}). Trying SSL...")

             
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port_ssl, timeout=20) as server:
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            print(f"✅ Email sent (SSL) to {to_email}")
            return True

        except smtplib.SMTPAuthenticationError as e_auth:
            print("❌ SMTP authentication error. For Gmail, use a generated App Password.")
            print(f"   Details: {e_auth}")
            return False
        except Exception as e:
            print(f"❌ Email sending error: {e}")
            return False

    # -------------------------- Public APIs --------------------------

    def send_email(self, to_email, subject, body):
        """Backwards-compatible: body is full HTML."""
        return self._send(to_email, subject, body)

     
    def send_appointment_booking_notification(self, patient_email, patient_name, doctor_name, appointment_date, appointment_time):
        subject = f"📅 Appointment Booked - {self.hospital_name}"
        content = f"""
            <p style="margin:0 0 12px 0;font-size:15px;color:#2c3e50;">
                Dear <strong>{patient_name}</strong>,
            </p>
            <p style="margin:0 0 10px 0;font-size:15px;color:#2c3e50;">
                Your appointment request has been received and is <strong>pending confirmation</strong> from
                <strong>{doctor_name}</strong>.
            </p>
            <div style="margin:14px 0;padding:12px 14px;border-left:4px solid #3498db;background:#f1f8ff;border-radius:6px;color:#1f2d3d;">
                <div><strong>Date:</strong> {appointment_date}</div>
                <div><strong>Time:</strong> {appointment_time}</div>
                <div><strong>Doctor:</strong> {doctor_name}</div>
            </div>
            <p style="margin:10px 0 0 0;font-size:14px;color:#2c3e50;">
                We’ll notify you as soon as the doctor approves or suggests a new time.
            </p>
        """
        html = self._frame_html("📅 Appointment Booked", "#3498db", content)
        return self._send(patient_email, subject, html)

     
    def send_appointment_confirmation(self, patient_email, patient_name, doctor_name, appointment_date, appointment_time, specialization):
        subject = f"✅ Appointment Confirmed - {self.hospital_name}"
        content = f"""
            <p style="margin:0 0 12px 0;font-size:15px;color:#2c3e50;">
                Dear <strong>{patient_name}</strong>,
            </p>
            <p style="margin:0 0 10px 0;font-size:15px;color:#2c3e50;">
                Your appointment has been <strong>confirmed</strong> with <strong>{doctor_name}</strong> ({specialization}).
            </p>
            <div style="margin:14px 0;padding:12px 14px;border-left:4px solid #27ae60;background:#eefaf2;border-radius:6px;color:#1f2d3d;">
                <div><strong>Date:</strong> {appointment_date}</div>
                <div><strong>Time:</strong> {appointment_time}</div>
            </div>
            <p style="margin:10px 0 0 0;font-size:14px;color:#2c3e50;">
                Please arrive 15 minutes early and carry any previous reports.
            </p>
        """
        html = self._frame_html("✅ Appointment Confirmed", "#27ae60", content)
        return self._send(patient_email, subject, html)

     
    def send_appointment_rejection(self, patient_email, patient_name, doctor_name, appointment_date, appointment_time, reason=None):
        subject = f"⚠️ Appointment Update - {self.hospital_name}"
        reason_html = f"<div><strong>Reason:</strong> {reason}</div>" if reason else ""
        content = f"""
            <p style="margin:0 0 12px 0;font-size:15px;color:#2c3e50;">
                Dear <strong>{patient_name}</strong>,
            </p>
            <p style="margin:0 0 10px 0;font-size:15px;color:#2c3e50;">
                We regret to inform you that your appointment with <strong>{doctor_name}</strong> was <strong>declined</strong>.
            </p>
            <div style="margin:14px 0;padding:12px 14px;border-left:4px solid #e74c3c;background:#fff2f2;border-radius:6px;color:#1f2d3d;">
                <div><strong>Date:</strong> {appointment_date}</div>
                <div><strong>Time:</strong> {appointment_time}</div>
                {reason_html}
            </div>
            <p style="margin:10px 0 0 0;font-size:14px;color:#2c3e50;">
                You may book another slot or contact our support for assistance.
            </p>
        """
        html = self._frame_html("⚠️ Appointment Rejected", "#e74c3c", content)
        return self._send(patient_email, subject, html)