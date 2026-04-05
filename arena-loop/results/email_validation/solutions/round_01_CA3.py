import re

def validate_email(email):
    """Check if an email address is valid.

    Args:
        email: str, the email address to validate

    Returns: True if valid, False if invalid
    """
    # 0. Check input type
    if not isinstance(email, str):
        return False

    # 1. Check for leading/trailing whitespace (e.g., 'user@example.com\n')
    if email.strip() != email:
        return False

    # 2. Must contain exactly one '@' symbol (e.g., '@nodomain.com', 'user@@example.com')
    if email.count('@') != 1:
        return False

    local_part, domain_part = email.split('@')

    # 3. Local part validation
    # Cannot be empty (e.g., '@nodomain.com')
    if not local_part:
        return False
    # Cannot start or end with a dot (e.g., '.user@example.com', 'user.@example.com')
    if local_part.startswith('.') or local_part.endswith('.'):
        return False
    # Cannot contain consecutive dots (e.g., 'user..name@example.com')
    if '..' in local_part:
        return False
    # Check for allowed characters in local part.
    # RFC 5322 "atom" characters are allowed, plus '.' (with restrictions handled above).
    # This regex broadly covers valid characters and implicitly handles spaces (e.g., 'user @example.com').
    # Allowed characters: a-zA-Z0-9!#$%&'*+-/=?^_`{|}~ and literal dot.
    # Note: the dot is included in the character class, but its placement restrictions are handled by explicit checks.
    allowed_local_chars_pattern = r"a-zA-Z0-9.!#$%&'*+-/=?^_`{|}~"
    if not re.fullmatch(f"[{allowed_local_chars_pattern}]+", local_part):
        return False

    # 4. Domain part validation
    # Cannot be empty
    if not domain_part:
        return False
    # Cannot start or end with a dot (e.g., 'user@.com')
    if domain_part.startswith('.') or domain_part.endswith('.'):
        return False
    # Cannot contain consecutive dots (e.g., 'user@example..com')
    if '..' in domain_part:
        return False
    # Must contain at least one dot (e.g., 'user@example' - no TLD)
    if '.' not in domain_part:
        return False

    domain_labels = domain_part.split('.')

    # A domain like 'example.com' should yield ['example', 'com'], so at least 2 labels
    if len(domain_labels) < 2:
        return False

    for label in domain_labels:
        # Each label cannot be empty (e.g., from 'user@example..com' if split resulted in '')
        if not label:
            return False
        # Each label cannot start or end with a hyphen (e.g., 'user@-example.com')
        if label.startswith('-') or label.endswith('-'):
            return False
        # Check for valid characters in domain label (alphanumeric and hyphens only).
        # This implicitly covers spaces and other invalid characters in domain labels.
        if not re.fullmatch(r'[a-zA-Z0-9-]+', label):
            return False

    # TLD (Top-Level Domain) must have at least 2 characters (e.g., 'user@example.c')
    tld = domain_labels[-1]
    if len(tld) < 2:
        return False

    # If all checks pass
    return True