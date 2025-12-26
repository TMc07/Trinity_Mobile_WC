import smtplib
from email.message import EmailMessage
from pathlib import Path
import os
import datetime

timestamp = datetime.datetime.now().strftime("%Y%m%d")

def send_email_with_attachments(sender, password, recipient, subject, body, attachment_paths):
    msg = EmailMessage()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.set_content(body)

    for file_path in attachment_paths:
        file_path = Path(file_path)
        if file_path.exists():
            with open(file_path, 'rb') as f:
                file_data = f.read()
                msg.add_attachment(
                    file_data,
                    maintype='application',
                    subtype='octet-stream',
                    filename=file_path.name
                )
        else:
            print(f"Warning: {file_path} not found. Skipping attachment.")

    smtp_server = 'smtp.office365.com'
    smtp_port = 587

    with smtplib.SMTP(smtp_server, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(sender, password)
        smtp.send_message(msg)

    print("Email sent successfully.")

if __name__ == "__main__":
    sender = os.getenv('EMAIL_SENDER')
    password = os.getenv('EMAIL_PASSWORD')
    recipient = os.getenv('EMAIL_RECIPIENT')

    subject = "Automated Report"
    body = "Please find the attached reports."

    # Example: Attach CSVs generated in your repo or pipeline workspace
    attachments = [
        f"Marketer_Sums_{timestamp}.csv", 
        f"Patient_Itemized_{timestamp}.csv"
    ]

    send_email_with_attachments(sender, password, recipient, subject, body, attachments)
