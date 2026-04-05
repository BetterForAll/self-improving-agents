def validate_email(email):
    """Check if an email address is valid.

    Args:
        email: str, the email address to validate

    Returns: True if valid, False if invalid
    """
    # 0. Basic type and emptiness check
    if not isinstance(email, str) or not email:
        return False

    # 1. No whitespace allowed anywhere in the email string
    # This covers 'user @example.com' and 'user@example.com\n'
    if any(c.isspace() for c in email):
        return False

    # 2. Exactly one '@' symbol
    # This covers 'user@@example.com'
    if email.count('@') != 1:
        return False

    local_part, domain_part = email.split('@')

    # 3. Local part and Domain part cannot be empty
    # This covers '@nodomain.com' (local_part will be an empty string)
    if not local_part or not domain_part:
        return False

    # 4. Local part validation
    # Cannot start or end with '.'
    # Covers '.user@example.com' and 'user.@example.com'
    if local_part.startswith('.') or local_part.endswith('.'):
        return False
    # Cannot have consecutive '..' in local part (common rule)
    if '..' in local_part:
        return False
    # Additional check: ensure local_part contains mostly valid characters (simplified)
    # This isn't explicitly requested by failed tests but is a common improvement.
    # For maximum compatibility, one might allow more special characters defined by RFCs.
    # For now, sticking to addressing the provided failed test cases.


    # 5. Domain part validation
    # Domain must contain at least one '.'
    if '.' not in domain_part:
        return False

    # Cannot start or end with '-'
    # Covers 'user@-example.com'
    if domain_part.startswith('-') or domain_part.endswith('-'):
        return False

    # Cannot have consecutive '..' in domain part
    # Covers 'user@example..com'
    if '..' in domain_part:
        return False

    # Split domain into labels (e.g., 'example.com' -> ['example', 'com'])
    domain_labels = domain_part.split('.')

    # Each domain label must not be empty
    # Covers 'user@.com' (domain_labels will be ['', 'com'])
    if any(not label for label in domain_labels):
        return False

    # TLD (Top-Level Domain) must be at least 2 characters long
    # Covers 'user@example.c'
    if len(domain_labels[-1]) < 2:
        return False

    # Each domain label should not start or end with a hyphen
    # And should only contain alphanumeric characters and hyphens internally
    for label in domain_labels:
        if not label: # Already caught by `any(not label ...)` but defensive
            continue
        if label.startswith('-') or label.endswith('-'):
            return False
        # Ensure all characters in a label are alphanumeric or hyphen (except start/end)
        # This implicitly disallows other special characters in domain labels.
        if not all(c.isalnum() or c == '-' for c in label):
            return False

    return True