import re

def validate_email(email):
    """Check if an email address is valid.

    Args:
        email: str, the email address to validate

    Returns: True if valid, False if invalid
    """
    # 1. Check for leading/trailing whitespace
    if email.strip() != email:
        return False

    # 2. Check for internal spaces
    if ' ' in email:
        return False

    # 3. Must contain exactly one '@' symbol
    if email.count('@') != 1:
        return False

    local_part, domain_part = email.split('@')

    # 4. Local part validation
    # Must not be empty
    if not local_part:
        return False
    # Must not start or end with a dot
    if local_part.startswith('.') or local_part.endswith('.'):
        return False
    # Must not contain consecutive dots
    if '..' in local_part:
        return False

    # 5. Domain part validation
    # Must not be empty
    if not domain_part:
        return False
    # Must contain at least one dot
    if '.' not in domain_part:
        return False
    # Must not start or end with a dot
    if domain_part.startswith('.') or domain_part.endswith('.'):
        return False
    # Must not contain consecutive dots
    if '..' in domain_part:
        return False

    # Split domain into labels (e.g., "example.com" -> ["example", "com"])
    domain_labels = domain_part.split('.')

    # Check each domain label
    for label in domain_labels:
        # Each label must not be empty (this is covered by previous '..' checks or start/end with dot)
        if not label:
            return False
        # Each label must not start or end with a hyphen
        if label.startswith('-') or label.endswith('-'):
            return False
        # (Optional but common: each label should only contain alphanumeric characters and hyphens.
        # This is not strictly required by the failed cases, but a more robust check)
        # if not re.fullmatch(r'[a-zA-Z0-9-]+', label):
        #    return False

    # 6. Top-Level Domain (TLD) length
    # TLD is the last part of the domain after the last dot
    tld = domain_labels[-1]
    if len(tld) < 2:
        return False

    return True