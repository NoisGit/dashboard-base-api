"""Email service for sending emails via SMTP."""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Environment, FileSystemLoader

from src.config.config import settings

logger = logging.getLogger(__name__)

template_env = Environment(
    loader=FileSystemLoader(
        os.path.join(os.path.dirname(__file__), "../templates/email")
    ),
    autoescape=True,
)


class EmailService:
    """
    EmailService provides functionality to send emails using SMTP.
    """

    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL

    def send_templated_email(
        self, to_email: str, subject: str, template_name: str, context: dict
    ):
        """Send an email using a specified template and context."""

        try:
            template = template_env.get_template(template_name)
            html_content = template.render(**context)

            txt_template_name = template_name.replace(".html", ".txt")

            try:
                txt_template = template_env.get_template(txt_template_name)
                text_content = txt_template.render(**context)

            except Exception:  # pylint: disable=broad-except
                text_content = "Por favor habilita la vista HTML para ver este mensaje."

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            msg.attach(MIMEText(text_content, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            if settings.EMAIL_DELIVERY_MODE.lower() == "log":
                logger.info("transactional_email_rendered template=%s", template_name)
                return

            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=20) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, msg.as_string())
            logger.info("transactional_email_sent template=%s", template_name)

        except Exception:  # pylint: disable=broad-except
            logger.exception("transactional_email_failed template=%s", template_name)
            raise
