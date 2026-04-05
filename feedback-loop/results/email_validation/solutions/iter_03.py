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
    # Allowed characters: alphanumeric, and !#$%&'*+-/=?^_`{|}~
    # Dots are allowed, but not at start/end, and not consecutive.
    # This regex ensures:
    # - Starts with one or more valid local characters (non-dot).
    # - Optionally followed by a sequence of a dot and one or more valid local characters (non-dot).
    # This implicitly disallows leading/trailing dots and consecutive dots.
    # This implementation focuses on the common "dot-atom" local part and does not
    # support "quoted-string" local parts (e.g., "John Doe"@example.com) for practical reasons,
    # as they are rare and complex to validate.
    local_part_pattern = r"^[a-zA-Z0-9!#$%&'*+-/=?^_`{|}~]+(?:\.[a-zA-Z0-9!#$%&'*+-/=?^_`{|}~]+)*$"
    if not re.fullmatch(local_part_pattern, local_part):
        return False

    # --- Domain Part Validation ---
    # 1. No leading/trailing dots, no consecutive dots in the domain part.
    if domain_part.startswith('.') or domain_part.endswith('.') or '..' in domain_part:
        return False

    # Split domain into labels (e.g., "example.com" -> ["example", "com"])
    domain_labels = domain_part.split('.')

    # 2. Domain must have at least two labels (e.g., "example.com" is valid, "example" is not for public email)
    if len(domain_labels) < 2:
        return False

    # 3. Validate each label in the domain part
    for label in domain_labels:
        if not label: # Empty label (e.g., "example..com" would result in an empty string in labels)
            return False
        if len(label) > 63: # Each label max 63 characters (RFC 1035)
            return False
        # Each label must start and end with an alphanumeric character.
        # Can contain alphanumeric characters or hyphens in between.
        # Examples: "example", "sub-domain", "test123" are valid labels.
        # "-example", "example-" are invalid.
        # This regex strictly follows RFC 1035 for hostname labels.
        label_pattern = r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$"
        if not re.fullmatch(label_pattern, label):
            return False

    # 4. TLD (Top-Level Domain) validation
    # TLD is the last label. Must be at least 2 characters long.
    # It has already been validated against `label_pattern` in the loop above to ensure
    # it contains valid characters (alphanumeric and hyphens, not starting/ending with hyphen).
    # The previous version's `tld.isalpha()` check was too restrictive for modern TLDs
    # which can contain hyphens (e.g., .co.uk, .foo-bar).
    tld = domain_labels[-1]
    if len(tld) < 2:
        return False

    return True