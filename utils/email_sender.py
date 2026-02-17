"""
Email Sender Module

Handles sending OTP via email using Flask-Mail
"""

from flask import Flask, render_template_string
from flask_mail import Mail, Message
import os


# Initialize Mail (will be set up in app.py)
mail = Mail()


def init_mail(app):
    """
    Initialize Flask-Mail with app configuration

    Args:
        app: Flask application instance
    """
    global mail
    mail.init_app(app)


def send_otp_email(email, otp_code, resident_name, app=None):
    """
    Send OTP via email to resident

    Args:
        email (str): Recipient email address
        otp_code (str): The OTP code to send
        resident_name (str): Name of resident
        app: Flask application context (optional)

    Returns:
        tuple: (success: bool, message: str)
            - (True, "Email sent successfully") if successful
            - (False, error_message) if failed
    """
    try:
        # Import here to avoid circular imports
        from app import app as flask_app

        if not flask_app.config.get('MAIL_SERVER'):
            return False, "Email configuration not set up. Please contact support."

        # Create email subject and body
        subject = "Your OTP Code - Hostel Management System"

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 500px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                    <h2 style="color: #007bff; margin-bottom: 20px;">Hostel Management System</h2>

                    <p>Hello <strong>{resident_name}</strong>,</p>

                    <p>You requested to login to your account. Here's your One-Time Password (OTP):</p>

                    <div style="background-color: #f0f0f0; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                        <p style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #007bff; margin: 0;">
                            {otp_code}
                        </p>
                    </div>

                    <p style="color: #666;">
                        <strong>This OTP is valid for 10 minutes only.</strong>
                    </p>

                    <p style="color: #666;">
                        If you didn't request this login, please ignore this email and ensure your account is secure.
                    </p>

                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">

                    <p style="color: #999; font-size: 12px;">
                        This is an automated email. Please do not reply to this message.
                    </p>
                </div>
            </body>
        </html>
        """

        # Create message
        msg = Message(
            subject=subject,
            recipients=[email],
            html=html_body,
            sender=flask_app.config.get('SENDER_EMAIL', 'noreply@hostelmanagement.com')
        )

        # Send email
        mail.send(msg)
        return True, "OTP sent successfully to your email"

    except Exception as e:
        error_msg = f"Failed to send OTP: {str(e)}"
        print(f"Email Error: {error_msg}")
        return False, "Failed to send OTP. Please try again later."


def send_test_email(email):
    """
    Send a test email to verify email configuration

    Args:
        email (str): Recipient email address

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        from app import app as flask_app

        if not flask_app.config.get('MAIL_SERVER'):
            return False, "Email server not configured"

        msg = Message(
            subject="Test Email - Hostel Management System",
            recipients=[email],
            body="This is a test email. If you received this, email configuration is working correctly.",
            sender=flask_app.config.get('SENDER_EMAIL', 'noreply@hostelmanagement.com')
        )

        mail.send(msg)
        return True, "Test email sent successfully"

    except Exception as e:
        return False, f"Failed to send test email: {str(e)}"
