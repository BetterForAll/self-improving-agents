import re

def validate_email(email):
    """Check if an email address is valid.

    Args:
        email: str, the email address to validate

    Returns: True if valid, False if invalid
    """
    # 1. Overall length check (RFC 5321 specifies 254 characters max)
    if len(email) > 254:
        return False

    # 2. Must contain exactly one '@' symbol
    if email.count('@') != 1:
        return False

    local_part, domain_part = email.split('@')

    # 3. Local and domain parts must not be empty
    if not local_part or not domain_part:
        return False

    # 4. Local part length check (RFC 5321 specifies max 64 characters)
    if len(local_part) > 64:
        return False

    # 5. Domain part length check (RFC 5321 specifies max 255 characters, including dots)
    if len(domain_part) > 255:
        return False

    # --- Local Part Validation ---
    # Allowed characters for unquoted local part: alphanumeric, and !#$%&'*+-/=?^_`{|}~
    # Dots are allowed, but not at start/end, and not consecutive.
    # This regex ensures:
    # - Starts with one or more valid local characters (non-dot).
    # - Optionally followed by a sequence of a dot and one or more valid local characters (non-dot).
    # This implicitly disallows leading/trailing dots and consecutive dots.
    # Note: This validator does NOT support quoted strings in the local part, which are allowed by RFC 5322
    # but are rare in practice and significantly complicate validation.
    local_part_pattern = r"^[a-zA-Z0-9!#$%&'*+-/=?^_`{|}~]+(?:\.[a-zA-Z0-9!#$%&'*+-/=?^_`{|}~]+)*$"
    if not re.fullmatch(local_part_pattern, local_part):
        return False

    # --- Domain Part Validation ---
    # 1. No leading/trailing dots, no consecutive dots in the domain part.
    if domain_part.startswith('.') or domain_part.endswith('.') or '..' in domain_part:
        return False

    # Split domain into labels (e.g., "example.com" -> ["example", "com"])
    domain_labels = domain_part.split('.')

    # 2. Domain must have at least two labels (e.g., "example.com" is valid, "example" is not for email)
    # This implies a Top-Level Domain (TLD) exists.
    if len(domain_labels) < 2:
        return False

    # 3. Validate each label in the domain part
    # Each label must start and end with an alphanumeric character.
    # Can contain alphanumeric characters or hyphens in between.
    # Max 63 characters (RFC 1035).
    # This regex supports Punycode IDN labels (e.g., xn--...) as they conform to ASCII label rules.
    label_pattern = r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$"
    for label in domain_labels:
        if not label: # Empty label (e.g., "example..com" would result in an empty string in labels)
            return False
        if len(label) > 63: # Each label max 63 characters (RFC 1035)
            return False
        if not re.fullmatch(label_pattern, label):
            return False

    # 4. TLD (Top-Level Domain) validation
    # TLD is the last label. It must conform to the general label rules (checked in the loop above).
    tld = domain_labels[-1]
    # Practical rule: TLDs must be at least 2 characters long.
    # (The original `not tld.isalpha()` check was too restrictive, as TLDs can contain numbers,
    # e.g., in Punycode or certain gTLDs like .jobs or .zone).
    if len(tld) < 2:
        return False
    # Additional practical rule: TLDs are generally not purely numeric.
    # This helps avoid ambiguity with IP address literals or purely numeric internal domains.
    if tld.isdigit():
        return False

    return True