"""Email templates for job match notifications."""

from typing import Any, Dict, Optional, Tuple
from app.notifications.config import EMAIL_TEMPLATE_VERSION


def render_match_email(
    job_data: Dict[str, Any],
    match_data: Dict[str, Any],
    recipient_name: Optional[str] = None,
) -> Tuple[str, str, str]:
    """Render subject, plain text, and HTML body for a job match alert.

    Returns:
        (subject, plain_text, html_body)
    """
    job_title = job_data.get("title", "New Job Opportunity")
    company_name = job_data.get("company_name", "Company")
    location = job_data.get("location") or "Not specified"
    workplace_type = job_data.get("workplace_type") or "Not specified"
    app_url = job_data.get("application_url") or "#"

    score = match_data.get("score", 0.0)
    matched_criteria = match_data.get("matched_criteria") or []
    missing_criteria = match_data.get("missing_criteria") or []
    explanation = match_data.get("explanation") or {}
    summary = explanation.get("summary") if isinstance(explanation, dict) else None

    greeting = f"Hello {recipient_name}," if recipient_name else "Hello,"

    subject = f"[{score:.0f}% Match] {job_title} at {company_name}"

    # Plain text version
    text_lines = [
        greeting,
        "",
        f"A new position matching your profile has been detected on JobWatch AI:",
        "",
        f"Position: {job_title}",
        f"Company:  {company_name}",
        f"Location: {location} ({workplace_type})",
        f"Match:    {score:.0f}%",
        "",
    ]

    if summary:
        text_lines.extend(["Overview:", summary, ""])

    if matched_criteria:
        text_lines.append("Key Matched Qualifications:")
        for item in matched_criteria[:5]:
            text_lines.append(f" - {item}")
        text_lines.append("")

    if missing_criteria:
        text_lines.append("Requirement Gaps:")
        for item in missing_criteria[:3]:
            text_lines.append(f" - {item}")
        text_lines.append("")

    text_lines.extend([
        f"View and Apply: {app_url}",
        "",
        "---",
        "JobWatch AI — Automated Career Portal Monitoring",
        f"Template Version: {EMAIL_TEMPLATE_VERSION}",
    ])

    plain_text = "\n".join(text_lines)

    # Clean HTML version
    matched_html = "".join(f"<li>{m}</li>" for m in matched_criteria[:5]) if matched_criteria else "<li>Profile meets basic prerequisites.</li>"
    missing_html = "".join(f"<li>{m}</li>" for m in missing_criteria[:3]) if missing_criteria else "<li>No critical gaps noted.</li>"
    summary_html = f"<p style='color: #4b5563; font-style: italic;'>{summary}</p>" if summary else ""

    html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{subject}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1f2937; max-width: 600px; margin: 0 auto; padding: 20px;">
  <div style="background: #2563eb; color: #ffffff; padding: 16px 24px; border-radius: 8px 8px 0 0;">
    <h1 style="margin: 0; font-size: 20px;">JobWatch AI Match Alert</h1>
  </div>
  <div style="border: 1px solid #e5e7eb; border-top: none; padding: 24px; border-radius: 0 0 8px 8px;">
    <p>{greeting}</p>
    <p>A new role matching your criteria has been detected:</p>

    <div style="background: #f3f4f6; padding: 16px; border-radius: 6px; margin: 16px 0;">
      <h2 style="margin: 0 0 8px 0; font-size: 18px; color: #111827;">{job_title}</h2>
      <p style="margin: 4px 0;"><strong>Company:</strong> {company_name}</p>
      <p style="margin: 4px 0;"><strong>Location:</strong> {location} ({workplace_type})</p>
      <p style="margin: 4px 0; color: #059669; font-size: 16px;"><strong>Match Score:</strong> {score:.0f}%</p>
    </div>

    {summary_html}

    <h3 style="font-size: 14px; text-transform: uppercase; color: #6b7280; margin-top: 16px;">Key Matches</h3>
    <ul style="margin: 8px 0 16px 20px; color: #047857;">
      {matched_html}
    </ul>

    <h3 style="font-size: 14px; text-transform: uppercase; color: #6b7280; margin-top: 16px;">Potential Gaps</h3>
    <ul style="margin: 8px 0 16px 20px; color: #b45309;">
      {missing_html}
    </ul>

    <div style="margin-top: 24px; text-align: center;">
      <a href="{app_url}" style="background: #2563eb; color: #ffffff; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold; display: inline-block;">View Opportunity</a>
    </div>

    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0 16px 0;" />
    <p style="font-size: 12px; color: #9ca3af; text-align: center; margin: 0;">
      JobWatch AI &bull; Automated Career Portal Monitoring &bull; v{EMAIL_TEMPLATE_VERSION}
    </p>
  </div>
</body>
</html>"""

    return subject, plain_text, html_body
