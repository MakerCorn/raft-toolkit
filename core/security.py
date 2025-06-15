"""
Security utilities and configuration for RAFT Toolkit.
"""

import os
import secrets
import string
from pathlib import Path
from typing import Optional, Set


class SecurityConfig:
    """Security configuration and validation."""

    # File upload restrictions
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {".pdf", ".txt", ".json", ".pptx"}

    # Path restrictions
    FORBIDDEN_PATHS = {"/etc", "/proc", "/sys", "/dev", "/root", "/home"}

    @classmethod
    def validate_file_path(cls, file_path: str) -> bool:
        """Validate that file path is safe."""
        try:
            path = Path(file_path).resolve()

            # Check for forbidden paths
            for forbidden in cls.FORBIDDEN_PATHS:
                if str(path).startswith(forbidden):
                    return False

            # Must be within allowed directories
            temp_dir = Path("/tmp").resolve()
            current_dir = Path.cwd().resolve()

            return str(path).startswith(str(temp_dir)) or str(path).startswith(str(current_dir))

        except (OSError, ValueError):
            return False

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename to prevent path traversal and other attacks."""
        if not filename:
            return "uploaded_file"

        # Remove path separators and control characters
        safe_chars = set(string.ascii_letters + string.digits + "._-")
        sanitized = "".join(c for c in filename if c in safe_chars)

        # Ensure we have something left
        if not sanitized:
            return "uploaded_file"

        # Limit length
        return sanitized[:100]

    @classmethod
    def generate_secure_id(cls, length: int = 32) -> str:
        """Generate cryptographically secure random ID."""
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    @classmethod
    def validate_api_key(cls, api_key: str) -> bool:
        """Validate API key format (basic validation)."""
        if not api_key:
            return False

        # Basic format checks
        if len(api_key) < 20:
            return False

        # Should not contain obvious placeholder text
        forbidden_values = {"test", "fake", "placeholder", "your_key_here"}
        if api_key.lower() in forbidden_values:
            return False

        return True

    @classmethod
    def get_secure_headers(cls) -> dict:
        """Get recommended security headers."""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": (
                "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
            ),
        }


def validate_environment() -> dict:
    """Validate security-relevant environment variables."""
    issues = []
    warnings = []

    # Check for development/debug settings in production
    if os.getenv("DEBUG", "").lower() in ("true", "1"):
        warnings.append("DEBUG mode is enabled - should be disabled in production")

    # Check for default/weak API keys
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key and not SecurityConfig.validate_api_key(openai_key):
        issues.append("OPENAI_API_KEY appears to be invalid or placeholder")

    # Check file permissions on sensitive files
    sensitive_files = [".env", "requirements.txt"]
    for file_path in sensitive_files:
        if Path(file_path).exists():
            stat = Path(file_path).stat()
            if stat.st_mode & 0o077:  # World or group readable
                warnings.append(f"{file_path} has overly permissive permissions")

    return {"issues": issues, "warnings": warnings, "secure": len(issues) == 0}
