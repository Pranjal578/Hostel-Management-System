"""
Email Sender Module

Handles sending OTP, payment notifications, and reminders via email using Flask-Mail.
Uses current_app to fetch mail configurations dynamically.
"""

from flask import current_app
from flask_mail import Mail, Message

mail = Mail()

def init_mail(app):
    """
    Initialize Flask-Mail with app configuration
    """
    global mail
    mail.init_app(app)


def send_otp_email(email, otp_code, user_name):
    """
    Send OTP via email to user for multi-factor login verification.
    """
    try:
        # Check if email is configured
        if not current_app.config.get('MAIL_SERVER'):
            return False, "Email configuration not set up on server."

        subject = "Your Verification Code - Hostel Management System"
        html_body = f"""
        <html>
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #1e293b; background-color: #f8fafc; padding: 20px;">
                <div style="max-width: 500px; margin: 0 auto; padding: 30px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                    <h2 style="color: #2563eb; margin-top: 0; font-weight: 700;">Hostel Management System</h2>
                    <p style="font-size: 16px;">Hello <strong>{user_name}</strong>,</p>
                    <p style="font-size: 15px;">You requested to log into your account. Use the following One-Time Password (OTP) to complete your authentication:</p>
                    <div style="background-color: #eff6ff; padding: 20px; border-radius: 10px; text-align: center; margin: 25px 0; border: 1px dashed #bfdbfe;">
                        <span style="font-size: 36px; font-weight: 800; letter-spacing: 6px; color: #2563eb;">
                            {otp_code}
                        </span>
                    </div>
                    <p style="color: #64748b; font-size: 14px;"><strong>This OTP is valid for 10 minutes only.</strong></p>
                    <p style="color: #94a3b8; font-size: 13px; margin-top: 30px; border-top: 1px solid #f1f5f9; padding-top: 20px;">
                        If you did not request this login, please change your password immediately.
                    </p>
                </div>
            </body>
        </html>
        """

        msg = Message(
            subject=subject,
            recipients=[email],
            html=html_body,
            sender=current_app.config.get('SENDER_EMAIL', 'noreply@hostelmanagement.com')
        )

        mail.send(msg)
        return True, "OTP email sent successfully."
    except Exception as e:
        error_msg = f"Failed to send OTP email: {str(e)}"
        print(error_msg)
        return False, error_msg


def send_payment_submitted_email(owner_email, resident_name, amount, review_url):
    """
    Notify a Hostel Owner that a resident has uploaded a payment receipt screenshot.
    """
    try:
        if not current_app.config.get('MAIL_SERVER'):
            return False, "Email configuration not set up."

        subject = f"New Payment Submitted - {resident_name}"
        html_body = f"""
        <html>
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #1e293b; background-color: #f8fafc; padding: 20px;">
                <div style="max-width: 500px; margin: 0 auto; padding: 30px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                    <h2 style="color: #2563eb; margin-top: 0; font-weight: 700;">Payment Verification Required</h2>
                    <p style="font-size: 15px;">Hello Hostel Owner,</p>
                    <p style="font-size: 15px;">Resident <strong>{resident_name}</strong> has submitted a payment receipt of amount <strong>${amount}</strong> for verification.</p>
                    <div style="margin: 25px 0; text-align: center;">
                        <a href="{review_url}" style="background-color: #2563eb; color: #ffffff; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 15px; display: inline-block;">
                            Review Payment Request
                        </a>
                    </div>
                    <p style="color: #64748b; font-size: 13px;">
                        If you cannot click the button above, copy and paste this link in your browser:<br>
                        <a href="{review_url}" style="color: #2563eb;">{review_url}</a>
                    </p>
                </div>
            </body>
        </html>
        """

        msg = Message(
            subject=subject,
            recipients=[owner_email],
            html=html_body,
            sender=current_app.config.get('SENDER_EMAIL', 'noreply@hostelmanagement.com')
        )

        mail.send(msg)
        return True, "Payment notification sent to owner."
    except Exception as e:
        error_msg = f"Failed to send payment submission email: {str(e)}"
        print(error_msg)
        return False, error_msg


def send_payment_status_email(resident_email, resident_name, amount, status, reason=None):
    """
    Notify a resident when their payment has been Verified or Rejected.
    """
    try:
        if not current_app.config.get('MAIL_SERVER'):
            return False, "Email configuration not set up."

        status_color = "#16a34a" if status == "Verified" else "#dc2626"
        subject = f"Rent Payment Receipt Status: {status}"
        
        reason_html = f"<p><strong>Message from Owner:</strong> {reason}</p>" if reason and status == "Rejected" else ""
        
        html_body = f"""
        <html>
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #1e293b; background-color: #f8fafc; padding: 20px;">
                <div style="max-width: 500px; margin: 0 auto; padding: 30px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                    <h2 style="color: #2563eb; margin-top: 0; font-weight: 700;">Payment Status Update</h2>
                    <p style="font-size: 15px;">Hello <strong>{resident_name}</strong>,</p>
                    <p style="font-size: 15px;">Your submitted payment of amount <strong>${amount}</strong> has been updated to:</p>
                    <div style="background-color: #f8fafc; border-left: 5px solid {status_color}; padding: 15px 20px; border-radius: 4px; margin: 20px 0;">
                        <span style="font-size: 18px; font-weight: 700; color: {status_color}; text-transform: uppercase;">
                            {status}
                        </span>
                    </div>
                    {reason_html}
                    <p style="font-size: 14px; color: #64748b; margin-top: 25px;">
                        Check your dashboard to view receipt logs or download verified payment history.
                    </p>
                </div>
            </body>
        </html>
        """

        msg = Message(
            subject=subject,
            recipients=[resident_email],
            html=html_body,
            sender=current_app.config.get('SENDER_EMAIL', 'noreply@hostelmanagement.com')
        )

        mail.send(msg)
        return True, "Payment status email sent."
    except Exception as e:
        error_msg = f"Failed to send payment status email: {str(e)}"
        print(error_msg)
        return False, error_msg


def send_payment_reminder_email(resident_email, resident_name, hostel_name, amount):
    """
    Send an automated outstanding rent email reminder to a resident.
    """
    try:
        if not current_app.config.get('MAIL_SERVER'):
            return False, "Email configuration not set up."

        subject = "Rent Payment Reminder - Action Required"
        html_body = f"""
        <html>
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #1e293b; background-color: #f8fafc; padding: 20px;">
                <div style="max-width: 500px; margin: 0 auto; padding: 30px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
                    <h2 style="color: #2563eb; margin-top: 0; font-weight: 700;">Rent Overdue Reminder</h2>
                    <p style="font-size: 15px;">Hello <strong>{resident_name}</strong>,</p>
                    <p style="font-size: 15px;">This is a friendly reminder that your rent for the current month at <strong>{hostel_name}</strong> is currently pending.</p>
                    <p style="font-size: 15px; font-weight: 600;">Monthly Rent Amount: ${amount}</p>
                    <p style="font-size: 15px;">Please log into your resident settings dashboard to download the payment QR code, make the transaction, and upload the transaction screenshot receipt.</p>
                    <div style="margin: 25px 0; text-align: center;">
                        <a href="{current_app.config.get('BASE_URL')}/resident/login" style="background-color: #2563eb; color: #ffffff; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 15px; display: inline-block;">
                            Go to Login Dashboard
                        </a>
                    </div>
                </div>
            </body>
        </html>
        """

        msg = Message(
            subject=subject,
            recipients=[resident_email],
            html=html_body,
            sender=current_app.config.get('SENDER_EMAIL', 'noreply@hostelmanagement.com')
        )

        mail.send(msg)
        return True, "Reminder email sent."
    except Exception as e:
        error_msg = f"Failed to send reminder email: {str(e)}"
        print(error_msg)
        return False, error_msg


def send_test_email(email):
    """
    Send a test email to verify configuration.
    """
    try:
        if not current_app.config.get('MAIL_SERVER'):
            return False, "Email server not configured"

        msg = Message(
            subject="Test Email - Hostel Management System",
            recipients=[email],
            body="This is a test email. If you received this, email configuration is working correctly.",
            sender=current_app.config.get('SENDER_EMAIL', 'noreply@hostelmanagement.com')
        )

        mail.send(msg)
        return True, "Test email sent successfully"
    except Exception as e:
        return False, f"Failed to send test email: {str(e)}"
