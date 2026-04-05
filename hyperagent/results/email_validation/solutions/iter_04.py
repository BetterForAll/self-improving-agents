import re

def validate_email(email):
    """Check if an email address is valid.

    Args:
        email: str, the email address to validate

    Returns: True if valid, False if invalid
    """
    # Added type check for robustness, ensuring the input is a string.
    if not isinstance(email, str):
        return False

    # Overall length check (RFC 5321 specifies max 254 characters for an email address)
    if len(email) > 254:
        return False

    # 1. Basic structural checks: must contain exactly one '@' and no spaces
    if " " in email:
        return False
    if email.count('@') != 1:
        return False

    local_part, domain_part = email.split('@')

    # Local part max length check (RFC 5322 section 3.4.1 specifies max 64 characters)
    if len(local_part) > 64:
        return False

    # 2. Local part checks
    # The local part (before the '@') cannot start or end with a dot.
    if local_part.startswith('.') or local_part.endswith('.'):
        return False
    
    # The local part cannot have consecutive dots.
    if ".." in local_part:
        return False

    # Character validation for local part using regex.
    # This regex enforces the allowed characters: alphanumeric, `_`, `.`, `+`, `-`, `%`.
    # It also implicitly handles the "not empty" check as `+` requires at least one char.
    # The original `if not local_part:` check is now redundant.
    # Note: This is a common simplification and not fully RFC-compliant (which allows more characters),
    # but covers most widely accepted valid email local parts.
    if not re.fullmatch(r"^[a-zA-Z0-9._%+-]+$", local_part):
        return False

    # Domain part max length check (RFC 5322 section 3.4.1 specifies max 255 characters)
    if len(domain_part) > 255:
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
    
    # The previous check `if not all(len(s) > 0 for s in domain_subparts): return False`
    # is redundant because the dot checks above (`.` present, no start/end `.`, no `..`)
    # already guarantee that all resulting subparts will be non-empty.

    # Character and structure validation for each domain subpart (label) using regex.
    # Domain labels can contain alphanumeric characters and hyphens.
    # They cannot start or end with a hyphen.
    # Each label has a maximum length of 63 characters (RFC 1035).
    # The regex `r"^(?!-)[a-zA-Z0-9-]{1,63}(?<!-)$"` enforces these rules concisely.
    # The `re.compile` is used for slight efficiency gain if called repeatedly.
    domain_label_regex = re.compile(r"^(?!-)[a-zA-Z0-9-]{1,63}(?<!-)$")
    for subpart in domain_subparts:
        if not domain_label_regex.fullmatch(subpart):
            return False
        
    # 4. Top-Level Domain (TLD) checks
    # The TLD is the last part of the domain (e.g., "com" in "example.com").
    tld = domain_subparts[-1]
    
    # The TLD must be at least 2 characters long (e.g., "co" is valid, "c" is not).
    if len(tld) < 2:
        return False

    # If all checks pass, the email is considered valid.
    return True