import resend
from flask import current_app


def _get_resend_client():
    api_key = current_app.config.get('RESEND_API_KEY')
    if not api_key:
        raise RuntimeError("RESEND_API_KEY is not configured")
    resend.api_key = api_key


def send_verification_email(to_email: str, username: str, token: str) -> dict:
    """Send email verification link via Resend."""
    _get_resend_client()

    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:5173')
    from_address = current_app.config.get('EMAIL_FROM_ADDRESS', 'noreply@vibeaura.app')
    verification_url = f"{frontend_url}/verify-email?token={token}"

    params = {
        "from": f"VibeCheck <{from_address}>",
        "to": [to_email],
        "subject": "Verify your VibeCheck account",
        "html": _verification_html(username, verification_url),
    }

    response = resend.Emails.send(params)
    current_app.logger.info(f"Verification email sent to {to_email} (id={response.get('id', 'unknown')})")
    return response


def send_password_reset_email(to_email: str, username: str, token: str) -> dict:
    """Send password reset link via Resend."""
    _get_resend_client()

    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:5173')
    from_address = current_app.config.get('EMAIL_FROM_ADDRESS', 'noreply@vibeaura.app')
    reset_url = f"{frontend_url}/reset-password?token={token}"

    params = {
        "from": f"VibeCheck <{from_address}>",
        "to": [to_email],
        "subject": "Reset your VibeCheck password",
        "html": _reset_password_html(username, reset_url),
    }

    response = resend.Emails.send(params)
    current_app.logger.info(f"Password reset email sent to {to_email} (id={response.get('id', 'unknown')})")
    return response


def send_moderator_magic_link_email(to_email: str, username: str, token: str) -> dict:
    """Send moderator magic-link login email via Resend."""
    _get_resend_client()

    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:5173')
    from_address = current_app.config.get('EMAIL_FROM_ADDRESS', 'noreply@vibeaura.app')
    moderator_url = f"{frontend_url}/mod/{token}"

    params = {
        "from": f"VibeCheck <{from_address}>",
        "to": [to_email],
        "subject": "Your VibeCheck moderator sign-in link",
        "html": _moderator_magic_link_html(username, moderator_url),
    }

    response = resend.Emails.send(params)
    current_app.logger.info(f"Moderator magic link email sent to {to_email} (id={response.get('id', 'unknown')})")
    return response


def _verification_html(username: str, url: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0;padding:0;background-color:#0f0f0f;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0f0f0f;padding:40px 20px;">
            <tr><td align="center">
                <table width="480" cellpadding="0" cellspacing="0" style="background-color:#1a1a2e;border-radius:16px;overflow:hidden;">
                    <tr><td style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:32px;text-align:center;">
                        <h1 style="margin:0;color:#fff;font-size:28px;font-weight:700;">VibeCheck</h1>
                    </td></tr>
                    <tr><td style="padding:32px;">
                        <h2 style="margin:0 0 16px;color:#e0e0e0;font-size:20px;">Hey {username} &#128075;</h2>
                        <p style="margin:0 0 24px;color:#a0a0b0;font-size:15px;line-height:1.6;">
                            Welcome to VibeCheck! Verify your email to start discovering and sharing your vibe.
                        </p>
                        <table width="100%" cellpadding="0" cellspacing="0">
                            <tr><td align="center">
                                <a href="{url}" style="display:inline-block;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;text-decoration:none;padding:14px 40px;border-radius:8px;font-size:16px;font-weight:600;">
                                    Verify My Email
                                </a>
                            </td></tr>
                        </table>
                        <p style="margin:24px 0 0;color:#666;font-size:13px;line-height:1.5;">
                            This link expires in 24 hours. If you didn&rsquo;t create an account, ignore this email.
                        </p>
                    </td></tr>
                    <tr><td style="padding:20px 32px;border-top:1px solid #2a2a3e;text-align:center;">
                        <p style="margin:0;color:#555;font-size:12px;">&copy; 2026 VibeCheck &middot; vibeaura.app</p>
                    </td></tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """


def _reset_password_html(username: str, url: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0;padding:0;background-color:#0f0f0f;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0f0f0f;padding:40px 20px;">
            <tr><td align="center">
                <table width="480" cellpadding="0" cellspacing="0" style="background-color:#1a1a2e;border-radius:16px;overflow:hidden;">
                    <tr><td style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:32px;text-align:center;">
                        <h1 style="margin:0;color:#fff;font-size:28px;font-weight:700;">VibeCheck</h1>
                    </td></tr>
                    <tr><td style="padding:32px;">
                        <h2 style="margin:0 0 16px;color:#e0e0e0;font-size:20px;">Password Reset</h2>
                        <p style="margin:0 0 24px;color:#a0a0b0;font-size:15px;line-height:1.6;">
                            Hi {username}, we received a request to reset your password. Click below to choose a new one.
                        </p>
                        <table width="100%" cellpadding="0" cellspacing="0">
                            <tr><td align="center">
                                <a href="{url}" style="display:inline-block;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;text-decoration:none;padding:14px 40px;border-radius:8px;font-size:16px;font-weight:600;">
                                    Reset Password
                                </a>
                            </td></tr>
                        </table>
                        <p style="margin:24px 0 0;color:#666;font-size:13px;line-height:1.5;">
                            This link expires in 1 hour. If you didn&rsquo;t request a password reset, ignore this email.
                        </p>
                    </td></tr>
                    <tr><td style="padding:20px 32px;border-top:1px solid #2a2a3e;text-align:center;">
                        <p style="margin:0;color:#555;font-size:12px;">&copy; 2026 VibeCheck &middot; vibeaura.app</p>
                    </td></tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """


def _moderator_magic_link_html(username: str, url: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0;padding:0;background-color:#0f0f0f;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0f0f0f;padding:40px 20px;">
            <tr><td align="center">
                <table width="480" cellpadding="0" cellspacing="0" style="background-color:#1a1a2e;border-radius:16px;overflow:hidden;">
                    <tr><td style="background:linear-gradient(135deg,#1d976c 0%,#93f9b9 100%);padding:32px;text-align:center;">
                        <h1 style="margin:0;color:#0f0f0f;font-size:28px;font-weight:700;">Moderator Access</h1>
                    </td></tr>
                    <tr><td style="padding:32px;">
                        <h2 style="margin:0 0 16px;color:#e0e0e0;font-size:20px;">Hi {username},</h2>
                        <p style="margin:0 0 24px;color:#a0a0b0;font-size:15px;line-height:1.6;">
                            Use this one-time link to access the moderator area.
                        </p>
                        <table width="100%" cellpadding="0" cellspacing="0">
                            <tr><td align="center">
                                <a href="{url}" style="display:inline-block;background:linear-gradient(135deg,#1d976c 0%,#93f9b9 100%);color:#0f0f0f;text-decoration:none;padding:14px 40px;border-radius:8px;font-size:16px;font-weight:700;">
                                    Open Moderator Page
                                </a>
                            </td></tr>
                        </table>
                        <p style="margin:24px 0 0;color:#666;font-size:13px;line-height:1.5;">
                            This link expires in 1 hour. If you did not initiate this login, ignore this email.
                        </p>
                    </td></tr>
                    <tr><td style="padding:20px 32px;border-top:1px solid #2a2a3e;text-align:center;">
                        <p style="margin:0;color:#555;font-size:12px;">&copy; 2026 VibeCheck</p>
                    </td></tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """
