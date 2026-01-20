"""
EMAIL BRIEFING SERVICE
======================
Sends grant collaboration briefings to team members
TESTING MODE: All emails go to stevekrontz@gmail.com
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

app = FastAPI(title="IRIS Email Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TESTING MODE - ALL EMAILS GO HERE
TEST_EMAIL = "stevekrontz@gmail.com"
TESTING_MODE = True  # SET TO FALSE FOR PRODUCTION

# Email config - using environment variables
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")


class TeamMember(BaseModel):
    name: str
    institution: str
    field: str
    h_index: int
    citations: int
    role: str
    matchedKeywords: List[str]
    email: Optional[str] = None
    orcid: Optional[str] = None
    openalex_id: Optional[str] = None


class Grant(BaseModel):
    source: str
    id: str
    title: str
    agency: str
    keywords: List[str]
    amount_range: Optional[str] = None
    duration: Optional[str] = None
    deadline: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None


class BriefingRequest(BaseModel):
    grant: Grant
    team: List[TeamMember]
    sender_name: str
    sender_email: str
    sender_institution: str
    custom_message: Optional[str] = None


def generate_briefing_html(grant: Grant, team: List[TeamMember], recipient: TeamMember, sender_name: str, sender_institution: str, custom_message: str = None) -> str:
    """Generate HTML briefing email"""
    
    team_list = "\n".join([
        f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                <strong>{m.name}</strong><br>
                <span style="color: #6b7280; font-size: 14px;">{m.institution}</span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; color: #6b7280;">
                {m.role}
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                <span style="color: #7c3aed; font-weight: bold;">h={m.h_index}</span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; font-size: 13px;">
                {', '.join(m.matchedKeywords[:3])}
            </td>
        </tr>
        """
        for m in team
    ])
    
    keywords_html = " ".join([
        f'<span style="display: inline-block; background: #dcfce7; color: #166534; padding: 4px 12px; border-radius: 20px; margin: 2px; font-size: 13px;">{kw}</span>'
        for kw in grant.keywords
    ])
    
    custom_section = f"""
    <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; margin: 20px 0;">
        <strong>Personal Note from {sender_name}:</strong><br>
        <p style="margin: 8px 0 0 0; color: #92400e;">{custom_message}</p>
    </div>
    """ if custom_message else ""
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1f2937; max-width: 700px; margin: 0 auto; padding: 20px;">
        
        <div style="background: linear-gradient(135deg, #059669, #10b981); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 24px;">🔬 Research Collaboration Opportunity</h1>
            <p style="color: #d1fae5; margin: 10px 0 0 0;">IRIS Research Intelligence System</p>
        </div>
        
        <div style="background: white; padding: 30px; border: 1px solid #e5e7eb; border-top: none;">
            
            <p style="font-size: 16px;">Dear Dr. {recipient.name.split()[-1]},</p>
            
            <p>I'm reaching out because IRIS (Intelligent Research Information System) has identified you as an excellent potential collaborator for an upcoming grant opportunity. Based on your research expertise in <strong>{recipient.field}</strong>, I believe you would be a valuable addition to our team.</p>
            
            {custom_section}
            
            <div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <h2 style="color: #166534; margin: 0 0 15px 0; font-size: 18px;">
                    <span style="background: #dcfce7; padding: 4px 10px; border-radius: 4px; font-size: 12px; margin-right: 8px;">{grant.source}</span>
                    {grant.title}
                </h2>
                
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 15px;">
                    <div><strong>Agency:</strong> {grant.agency}</div>
                    <div><strong>Funding:</strong> {grant.amount_range or 'See announcement'}</div>
                    <div><strong>Duration:</strong> {grant.duration or 'Varies'}</div>
                    <div><strong>Deadline:</strong> {grant.deadline or 'Rolling'}</div>
                </div>
                
                <p style="margin: 10px 0; color: #374151;">{grant.description or ''}</p>
                
                <div style="margin-top: 15px;">
                    <strong>Key Research Areas:</strong><br>
                    {keywords_html}
                </div>
                
                {f'<p style="margin-top: 15px;"><a href="{grant.url}" style="color: #059669;">View Full Announcement →</a></p>' if grant.url else ''}
            </div>
            
            <h3 style="color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px;">Proposed Research Team</h3>
            
            <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <thead>
                    <tr style="background: #f3f4f6;">
                        <th style="padding: 12px; text-align: left; font-weight: 600;">Researcher</th>
                        <th style="padding: 12px; text-align: left; font-weight: 600;">Role</th>
                        <th style="padding: 12px; text-align: left; font-weight: 600;">Impact</th>
                        <th style="padding: 12px; text-align: left; font-weight: 600;">Expertise</th>
                    </tr>
                </thead>
                <tbody>
                    {team_list}
                </tbody>
            </table>
            
            <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <h3 style="color: #1e40af; margin: 0 0 10px 0; font-size: 16px;">Why This Team?</h3>
                <p style="margin: 0; color: #1e40af;">
                    This team was assembled by IRIS using semantic analysis of research profiles across {len(set(m.institution for m in team))} institution(s). 
                    The combination of expertise provides comprehensive coverage of the grant's focus areas while maximizing collective research impact 
                    (combined h-index: {sum(m.h_index for m in team)}).
                </p>
            </div>
            
            <h3 style="color: #1f2937;">Next Steps</h3>
            <ol style="color: #4b5563;">
                <li>Review the grant announcement linked above</li>
                <li>Let me know if you're interested in participating</li>
                <li>We'll schedule a brief call to discuss roles and timeline</li>
            </ol>
            
            <p>I'd love to discuss this opportunity with you. Please feel free to reply to this email or reach out at your convenience.</p>
            
            <p style="margin-top: 30px;">
                Best regards,<br>
                <strong>{sender_name}</strong><br>
                <span style="color: #6b7280;">{sender_institution}</span>
            </p>
            
        </div>
        
        <div style="background: #f3f4f6; padding: 20px; border-radius: 0 0 12px 12px; text-align: center; font-size: 12px; color: #6b7280;">
            <p style="margin: 0;">This collaboration opportunity was identified by <strong>IRIS</strong> - Intelligent Research Information System</p>
            <p style="margin: 5px 0 0 0;">Kennesaw State University | The BrainLab</p>
        </div>
        
    </body>
    </html>
    """


def generate_briefing_text(grant: Grant, team: List[TeamMember], recipient: TeamMember, sender_name: str, sender_institution: str, custom_message: str = None) -> str:
    """Generate plain text briefing email"""
    
    team_list = "\n".join([
        f"  • {m.name} ({m.institution}) - {m.role}, h={m.h_index}"
        for m in team
    ])
    
    custom_section = f"\n\nPersonal Note from {sender_name}:\n{custom_message}\n" if custom_message else ""
    
    return f"""
RESEARCH COLLABORATION OPPORTUNITY
===================================

Dear Dr. {recipient.name.split()[-1]},

I'm reaching out because IRIS (Intelligent Research Information System) has identified you as an excellent potential collaborator for an upcoming grant opportunity. Based on your research expertise in {recipient.field}, I believe you would be a valuable addition to our team.
{custom_section}

GRANT OPPORTUNITY
-----------------
{grant.source}: {grant.title}

Agency: {grant.agency}
Funding: {grant.amount_range or 'See announcement'}
Duration: {grant.duration or 'Varies'}
Deadline: {grant.deadline or 'Rolling'}

{grant.description or ''}

Key Research Areas: {', '.join(grant.keywords)}

{f'Full Announcement: {grant.url}' if grant.url else ''}


PROPOSED RESEARCH TEAM
----------------------
{team_list}

Combined h-index: {sum(m.h_index for m in team)}


NEXT STEPS
----------
1. Review the grant announcement linked above
2. Let me know if you're interested in participating
3. We'll schedule a brief call to discuss roles and timeline

I'd love to discuss this opportunity with you. Please feel free to reply to this email.

Best regards,
{sender_name}
{sender_institution}

---
This collaboration opportunity was identified by IRIS
Kennesaw State University | The BrainLab
"""


@app.post("/send-briefing")
async def send_briefing(request: BriefingRequest):
    """Send briefing emails to team members"""
    
    results = []
    
    for member in request.team:
        # In testing mode, all emails go to test address
        recipient_email = TEST_EMAIL if TESTING_MODE else (member.email or TEST_EMAIL)
        
        # Generate email content
        html_content = generate_briefing_html(
            request.grant,
            request.team,
            member,
            request.sender_name,
            request.sender_institution,
            request.custom_message
        )
        
        text_content = generate_briefing_text(
            request.grant,
            request.team,
            member,
            request.sender_name,
            request.sender_institution,
            request.custom_message
        )
        
        result = {
            "recipient": member.name,
            "intended_email": member.email or "unknown",
            "actual_email": recipient_email,
            "testing_mode": TESTING_MODE,
            "status": "pending"
        }
        
        # For now, just generate the email without sending
        # To actually send, configure SMTP credentials
        if SMTP_USER and SMTP_PASSWORD and not TESTING_MODE:
            try:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = f"Research Collaboration Opportunity: {request.grant.title}"
                msg['From'] = request.sender_email
                msg['To'] = recipient_email
                
                msg.attach(MIMEText(text_content, 'plain'))
                msg.attach(MIMEText(html_content, 'html'))
                
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.starttls()
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.send_message(msg)
                
                result["status"] = "sent"
            except Exception as e:
                result["status"] = "error"
                result["error"] = str(e)
        else:
            result["status"] = "preview_only"
            result["html_preview"] = html_content[:500] + "..."
        
        results.append(result)
    
    return {
        "success": True,
        "testing_mode": TESTING_MODE,
        "test_email": TEST_EMAIL if TESTING_MODE else None,
        "results": results,
        "message": f"{'[TEST MODE] ' if TESTING_MODE else ''}Processed {len(results)} briefings"
    }


@app.post("/preview-briefing")
async def preview_briefing(request: BriefingRequest):
    """Preview briefing without sending"""
    
    if not request.team:
        raise HTTPException(status_code=400, detail="No team members provided")
    
    # Generate preview for first team member
    member = request.team[0]
    
    html_content = generate_briefing_html(
        request.grant,
        request.team,
        member,
        request.sender_name,
        request.sender_institution,
        request.custom_message
    )
    
    return {
        "success": True,
        "preview_for": member.name,
        "html": html_content,
        "team_count": len(request.team),
        "testing_mode": TESTING_MODE,
        "test_email": TEST_EMAIL
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "testing_mode": TESTING_MODE,
        "test_email": TEST_EMAIL,
        "smtp_configured": bool(SMTP_USER and SMTP_PASSWORD)
    }


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("IRIS EMAIL BRIEFING SERVICE")
    print("=" * 60)
    print(f"TESTING MODE: {TESTING_MODE}")
    print(f"TEST EMAIL: {TEST_EMAIL}")
    print(f"All emails will be sent to: {TEST_EMAIL}")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8001)
