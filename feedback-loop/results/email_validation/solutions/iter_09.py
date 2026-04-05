import re

# Define character sets for clarity and potential reuse in regex patterns.
# LOCAL_PART_CHARS: Characters allowed in a 'dot-atom' local-part (RFC 5322 'atext').
LOCAL_PART_CHARS = r"a-zA-Z0-9!#$%&'*+-/=?^_`{|}~"
# DOMAIN_LABEL_CHARS: Characters allowed in a DNS hostname label (RFC 1035).
DOMAIN_LABEL_CHARS = r"a-zA-Z0-9"

# Pre-compile regex patterns for efficiency, as they are used repeatedly.
# Local part pattern:
# - Starts with one or more allowed 'atext' characters.
# - Optionally followed by a sequence of a dot and one or more 'atext' characters.
# - This implicitly disallows leading/trailing dots and consecutive dots.
LOCAL_PART_PATTERN = re.compile(rf"^[{LOCAL_PART_CHARS}]+(?:\.[{LOCAL_PART_CHARS}]+)*$")

# Domain label pattern (for each segment of the domain like "example" in "example.com"):
# - Must start and end with an alphanumeric character.
# - Can contain alphanumeric characters or hyphens in between.
# - This strictly follows RFC 1035 for hostname labels.
DOMAIN_LABEL_PATTERN = re.compile(rf"^[{DOMAIN_LABEL_CHARS}](?:[{DOMAIN_LABEL_CHARS}-]*[{DOMAIN_LABEL_CHARS}])?$")


def validate_email(email):
    """Check if an email address is valid.

    This function validates email addresses based on common practical standards
    derived from RFC 5321 (SMTP), RFC 5322 (Internet Message Format - specifically 'dot-atom' local parts),
    and RFC 1035 (DNS hostname labels).

    Args:
        email: str, the email address to validate

    Returns: True if valid, False if invalid
    """
    # Defensive check: Ensure input is a string.
    if not isinstance(email, str):
        return False

    # 1. Overall length check (RFC 5321 specifies 254 characters maximum for the address itself)
    if len(email) > 254:
        return False

    # 2. Must contain exactly one '@' symbol
    if email.count('@') != 1:
        return False

    local_part, domain_part = email.split('@')

    # 3. Local and domain parts must not be empty (e.g., "@domain.com" or "user@")
    if not local_part or not domain_part:
        return False

    # 4. Local part length check (RFC 5321 specifies maximum 64 characters)
    if len(local_part) > 64:
        return False

    # 5. Domain part length check (RFC 5321 specifies maximum 255 characters, including dots)
    # This refers to the string length of the domain part itself, aligning with common practices.
    if len(domain_part) > 255:
        return False

    # --- Local Part Validation ---
    # Allowed characters: alphanumeric, and !#$%&'*+-/=?^_`{|}~ (RFC 5322 'atext').
    # Dots are allowed, but not at start/end, and not consecutive.
    # This implementation focuses on the common "dot-atom" local part and does not
    # support "quoted-string" local parts (e.g., "John Doe"@example.com) or
    # Internationalized Email Addresses (EAI) for practical reasons, as they are
    # rare in typical web forms and complex to validate fully.
    if not LOCAL_PART_PATTERN.fullmatch(local_part):
        return False

    # --- Domain Part Validation ---
    # 1. No leading/trailing dots, no consecutive dots in the domain part.
    #    (These conditions are also implicitly handled by label validation, but provide an early exit.)
    if domain_part.startswith('.') or domain_part.endswith('.') or '..' in domain_part:
        return False

    # Split domain into labels (e.g., "example.com" -> ["example", "com"])
    domain_labels = domain_part.split('.')

    # 2. Domain must have at least two labels for public email addresses
    #    (e.g., "example.com" is valid, "example" or "localhost" are not accepted here).
    if len(domain_labels) < 2:
        return False

    # 3. Validate each label in the domain part
    for label in domain_labels:
        if not label: # Empty label (e.g., "example..com" or a trailing dot resulting in an empty string)
            return False
        if len(label) > 63: # Each label max 63 characters (RFC 1035)
            return False
        # Each label must conform to hostname label rules: start/end with alphanumeric,
        # can contain alphanumeric or hyphens in between.
        if not DOMAIN_LABEL_PATTERN.fullmatch(label):
            return False

    # 4. TLD (Top-Level Domain) validation
    # TLD is the last label. Must be at least 2 characters long (practical minimum).
    # It has already been validated against `DOMAIN_LABEL_PATTERN` in the loop above
    # to ensure it contains valid characters and structure.
    tld = domain_labels[-1]
    if len(tld) < 2:
        return False

    return True