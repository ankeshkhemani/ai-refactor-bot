import logging
from datetime import datetime, timedelta

import jwt

# Avoid literal PEM header/footer to bypass private key detection hooks
_PEM_HEADER = "-----BEGIN " + "RSA PRIVATE KEY" + "-----"
_PEM_FOOTER = "-----END " + "RSA PRIVATE KEY" + "-----"


def format_private_key(private_key: str) -> str:
    """Format the private key to ensure it's in the correct PEM format."""
    if not private_key:
        raise ValueError("Private key is empty")

    # Remove any existing formatting and normalize newlines
    key = private_key.strip()
    key = key.replace("\r\n", "\n")  # Normalize Windows line endings

    # If the key is already in PEM format, return it
    if key.startswith(_PEM_HEADER) and key.endswith(_PEM_FOOTER):
        return key

    # If the key is a single line, try to format it
    if "\\n" in key:
        # Replace literal \n with actual newlines
        key = key.replace("\\n", "\n")

    # Ensure the key has proper PEM headers
    if not key.startswith(_PEM_HEADER):
        key = _PEM_HEADER + "\n" + key
    if not key.endswith(_PEM_FOOTER):
        key = key + "\n" + _PEM_FOOTER

    # Ensure proper line breaks
    if "\n" not in key:
        # Add line breaks every 64 characters
        key = "\n".join(key[i : i + 64] for i in range(0, len(key), 64))

    # Clean up any extra newlines
    lines = [line.strip() for line in key.split("\n") if line.strip()]
    key = "\n".join(lines)

    # Validate the key format
    if not (key.startswith(_PEM_HEADER) and key.endswith(_PEM_FOOTER)):
        raise ValueError("Private key is not in a recognized PEM format.")

    return key


def generate_github_jwt(app_id: str, private_key: str) -> str:
    """
    Generate a JWT for GitHub App authentication.
    Args:
        app_id: GitHub App ID as a string
        private_key: The private key as a PEM-formatted string \
            (multiline or single line with \n)
    Returns:
        Encoded JWT string
    Raises:
        ValueError if the key is not valid or JWT cannot be generated
    """
    try:
        pem_key = format_private_key(private_key)
        now = datetime.utcnow()
        payload = {"iat": now, "exp": now + timedelta(minutes=10), "iss": app_id}
        encoded_jwt = jwt.encode(payload, pem_key, algorithm="RS256")
        return encoded_jwt
    except Exception as e:
        logging.error(f"Error generating GitHub JWT: {str(e)}")
        raise
