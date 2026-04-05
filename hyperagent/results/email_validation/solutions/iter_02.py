def validate_email(email):
    """Check if an email address is valid.

    Args:
        email: str, the email address to validate

    Returns: True if valid, False if invalid
    """
    # 1. Basic structural checks: must contain exactly one '@' and no spaces
    if " " in email:
        return False
    if email.count('@') != 1:
        return False

    local_part, domain_part = email.split('@')

    # 2. Local part checks
    # The local part (before the '@') cannot be empty.
    if not local_part:
        return False
    
    # NEW: The local part cannot start or end with a dot.
    if local_part.startswith('.') or local_part.endswith('.'):
        return False
    
    # NEW: The local part cannot have consecutive dots.
    if ".." in local_part:
        return False

    # NEW: Character validation for local part.
    # Common allowed characters: alphanumeric, `_`, `.`, `+`, `-`, `%`.
    # This is a common simplification and not fully RFC-compliant (which allows more characters),
    # but covers most widely accepted valid email local parts.
    allowed_local_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._%+-")
    for char in local_part:
        if char not in allowed_local_chars:
            return False

    # 3. Domain part checks
    # The domain part (after the '@') cannot be empty.
    if not domain_part:
        return False
    
    # The domain part must contain at least one dot (e.g., "example.com", not "example").
    if "." not in domain_part:
        return False
    
    # The domain part cannot start or end with a dot (e.g., "test@.com" or "test@example.").
    if domain_part.startswith('.') or domain_part.endswith('.'):
        return False
    
    # The domain part cannot have consecutive dots (e.g., "test@example..com").
    if ".." in domain_part:
        return False
        
    # Split the domain into subparts by the dot (e.g., "example.com" -> ["example", "com"])
    domain_subparts = domain_part.split('.')
    
    # Ensure all domain subparts are non-empty. This reinforces the checks above.
    if not all(len(s) > 0 for s in domain_subparts):
        return False
        
    # NEW: Character and structure validation for each domain subpart (label).
    # Domain labels can contain alphanumeric characters and hyphens.
    # They cannot start or end with a hyphen.
    # Also, each label has a maximum length of 63 characters (RFC 1035).
    allowed_domain_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-")
    for subpart in domain_subparts:
        # NEW: Max length for a domain label
        if len(subpart) > 63: 
            return False
        # NEW: Domain label cannot start or end with a hyphen
        if subpart.startswith('-') or subpart.endswith('-'):
            return False
        # NEW: Character validation for domain subparts
        for char in subpart:
            if char not in allowed_domain_chars:
                return False
        
    # 4. Top-Level Domain (TLD) checks
    # The TLD is the last part of the domain (e.g., "com" in "example.com").
    tld = domain_subparts[-1]
    
    # The TLD must be at least 2 characters long (e.g., "co" is valid, "c" is not).
    # The TLD should consist only of alphabetic characters (e.g., "com" is valid, "123" is not).
    if len(tld) < 2 or not tld.isalpha():
        return False

    # If all checks pass, the email is considered valid.
    return True