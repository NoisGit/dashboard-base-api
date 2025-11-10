"""
Firebase initialization module.

This module handles the initialization of Firebase Admin SDK with service account credentials
loaded from environment variables.
"""
import os
import json
import base64
import logging
import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials

logger = logging.getLogger(__name__)


def initialize_firebase():
    """Initializes Firebase Admin SDK with service account credentials."""
    try:
        load_dotenv()

        service_account_key_base64 = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
        if not service_account_key_base64:
            raise ValueError(
                "FIREBASE_SERVICE_ACCOUNT_KEY environment variable is not set")

        try:
            service_account_key_json = base64.b64decode(
                service_account_key_base64).decode("utf-8")
        except Exception as e:
            raise ValueError(f"Error al decodificar Base64: {e}") from e

        try:
            service_account_info = json.loads(service_account_key_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error al decodificar JSON: {e}") from e

        # Inicializar Firebase
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred)
        logger.info("✅ Firebase Admin SDK initialized successfully")
    except Exception as e:
        logger.error("❌ Failed to initialize Firebase Admin SDK: %s", str(e))
        raise e
