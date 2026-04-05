import re

def validate_email(email):
    """Check if an email address is valid.

    Args:
        email: str, the email address to validate

    Returns: True if valid, False if invalid
    """
    # 1. Overall length check (RFC 5321 specifies 254 characters max for the address itself)
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
    # Allowed characters for dot-atom: alphanumeric, and !#$%&'*+-/=?^_`{|}~
    # Dots are allowed as separators, but not at start/end, and not consecutive.
    # This regex ensures:
    # - Starts with one or more valid local characters (non-dot).
    # - Optionally followed by a sequence of a dot and one or more valid local characters (non-dot).
    # This implicitly disallows leading/trailing dots and consecutive dots.
    # This implementation focuses on the common "dot-atom" local part and does not
    # support "quoted-string" local parts (e.g., "John Doe"@example.com) or
    # obsoleted forms for practical reasons, as they are rare and complex to validate.
    local_part_allowed_chars = r"[a-zA-Z0-9!#$%&'*+-/=?^_`{|}~]"
    local_part_pattern = rf"^{local_part_allowed_chars}+(?:\.{local_part_allowed_chars}+)*$"
    if not re.fullmatch(local_part_pattern, local_part):
        return False

    # --- Domain Part Validation ---
    # Split domain into labels (e.g., "example.com" -> ["example", "com"])
    domain_labels = domain_part.split('.')

    # The `split('.')` and subsequent label validation implicitly handles:
    # - No leading/trailing dots (an empty string would appear at the start/end of `domain_labels`)
    # - No consecutive dots (an empty string would appear in the middle of `domain_labels`)
    #   These are caught by the `if not label:` check below.

    # 1. Domain must have at least two labels for public internet email (e.g., "example.com" is valid, "example" is not)
    # This excludes single-label domains like "localhost" which are valid in some contexts but not for general email.
    if len(domain_labels) < 2:
        return False

    # 2. Validate each label in the domain part (RFC 1035, RFC 1123)
    # This regex strictly follows hostname label rules:
    # - Must be at least 1 character long.
    # - Starts and ends with an alphanumeric character.
    # - Can contain alphanumeric characters or hyphens in between.
    # Examples: "example", "sub-domain", "test123" are valid labels.
    # "-example", "example-" are invalid.
    label_pattern = r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$"
    for label in domain_labels:
        if not label: # Catches empty labels from leading/trailing/consecutive dots (e.g., ".example.com", "example..com")
            return False
        if len(label) > 63: # Each label max 63 characters (RFC 1035)
            return False
        if not re.fullmatch(label_pattern, label):
            return False

    # 3. TLD (Top-Level Domain) validation
    # TLD is the last label. Must be at least 2 characters long.
    # It has already been validated against `label_pattern` in the loop above to ensure
    # it contains valid characters (alphanumeric and hyphens, not starting/ending with hyphen).
    # Modern TLDs can contain hyphens (e.g., .co.uk, .foo-bar).
    tld = domain_labels[-1]
    if len(tld) < 2:
        return False

    return True