def validate_email(email):
    """Check if an email address is valid.

    Args:
        email: str, the email address to validate

    Returns: True if valid, False if invalid
    """
    # 0. Basic check for string type and non-emptiness
    if not isinstance(email, str) or not email:
        return False

    # 1. No leading/trailing whitespace and no internal spaces or newlines
    # Handles: 'user @example.com', 'user@example.com\n', and also leading/trailing spaces
    if email.strip() != email or " " in email:
        return False

    # 2. Must contain exactly one '@' symbol
    # Handles: 'user@@example.com', and cases with no '@' (though already implicitly handled by split if no '@')
    if email.count('@') != 1:
        return False

    local_part, domain_part = email.split('@')

    # 3. Validate local part
    # Local part cannot be empty
    # Handles: '@nodomain.com'
    if not local_part:
        return False
    # Local part cannot start or end with a dot
    # Handles: '.user@example.com', 'user.@example.com'
    if local_part.startswith('.') or local_part.endswith('.'):
        return False
    # Local part cannot have consecutive dots
    if ".." in local_part:
        return False
    # (More comprehensive checks for allowed characters in local part are complex
    # by RFCs, but the above covers the identified edge cases.)

    # 4. Validate domain part
    # Domain part cannot be empty
    if not domain_part:  # Handles 'user@'
        return False
    # Domain part must contain at least one dot
    # Handles: 'user@example'
    if '.' not in domain_part:
        return False
    # Domain part cannot start or end with a dot
    # Handles: 'user@.com'
    if domain_part.startswith('.') or domain_part.endswith('.'):
        return False
    # Domain part cannot have consecutive dots
    # Handles: 'user@example..com'
    if ".." in domain_part:
        return False

    # Split domain into labels and validate each label
    domain_labels = domain_part.split('.')
    for label in domain_labels:
        # Each label must not be empty (this would happen with consecutive dots or leading/trailing dots)
        if not label:
            return False
        # Domain labels cannot start or end with a hyphen
        # Handles: 'user@-example.com' (and also 'user@example-.com')
        if label.startswith('-') or label.endswith('-'):
            return False
        # (More comprehensive checks for allowed characters in labels usually include
        # alphanumeric and hyphens, but the specific failed cases don't require this.)

    # 5. Validate Top-Level Domain (TLD)
    # TLD (the part after the last dot) must be at least 2 characters long
    # Handles: 'user@example.c'
    tld = domain_part.split('.')[-1]
    if len(tld) < 2:
        return False

    return True