"""
Generate .eml file that can be opened in email client
"""
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

def create_eml_file(to_email: str, subject: str, html_content: str, from_email: str = "stevekrontz@gmail.com"):
    """Create .eml file that can be opened in Outlook/Gmail"""
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
    
    # Plain text version
    text_content = "Please view this email in an HTML-capable email client."
    
    msg.attach(MIMEText(text_content, 'plain'))
    msg.attach(MIMEText(html_content, 'html'))
    
    return msg.as_string()


if __name__ == "__main__":
    # Read the generated HTML
    with open(r"C:\dev\research\project-iris\test_briefing.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Create EML file
    eml_content = create_eml_file(
        to_email="stevekrontz@gmail.com",
        subject="[IRIS TEST] Research Collaboration Opportunity: BRAIN Initiative",
        html_content=html_content,
        from_email="stevekrontz@gmail.com"
    )
    
    output_path = r"C:\dev\research\project-iris\test_briefing.eml"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(eml_content)
    
    print(f"Created: {output_path}")
    print("Double-click the .eml file to open in your email client and send!")
    
    # Try to open it
    os.startfile(output_path)
