"""Firebase compatibility shim.

Coredeck no longer uses Firebase. This module remains so older imports do not
cause runtime errors while notifications migrate to internal/Supabase-backed
services.
"""

import logging

logger = logging.getLogger(__name__)


def initialize_firebase() -> None:
    """No-op kept for backward compatibility with legacy startup code paths."""
    logger.info("Firebase is disabled; skipping legacy initialization.")
