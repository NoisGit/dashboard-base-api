"""Email service for sending emails via SMTP."""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader

from src.config.config import settings

logger = logging.getLogger(__name__)

template_env = Environment(
    loader=FileSystemLoader(os.path.join(
        os.path.dirname(__file__), "../templates/email")),
    autoescape=True
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
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict
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

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)

            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.from_email, to_email, msg.as_string())
            server.quit()

            logger.info(
                "📧 Correo %s enviado exitosamente a %s",
                subject, to_email
            )

        except Exception as e:  # pylint: disable=broad-except
            logger.error(
                "❌ Error enviando correo a %s: %s",
                to_email, str(e)
            )
