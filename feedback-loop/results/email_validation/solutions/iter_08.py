import re
import codecs # For IDN support in standard library

def validate_email(email):
    """Check if an email address is valid.

    Args:
        email: str, the email address to validate

    Returns: True if valid, False if invalid
    """
    # 1. Overall length check (RFC 5321 specifies 254 characters max for the address)
    # This checks the length of the string as received, which may contain Unicode.
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
    # Handle Internationalized Domain Names (IDN) by converting to Punycode.
    # The `codecs.encode(..., 'idna')` method correctly handles both Unicode and already Punycode domains.
    try:
        punycode_domain_part = codecs.encode(domain_part, 'idna').decode('ascii')
    except (UnicodeError, TypeError):
        # This catches cases where the domain part is not a valid IDN or contains invalid characters.
        return False

    # 5. Domain part length check for the Punycode form (RFC 1035 specifies max 255 characters for FQDN)
    if len(punycode_domain_part) > 255:
        return False

    # 1. No leading/trailing dots, no consecutive dots in the Punycode domain part.
    if punycode_domain_part.startswith('.') or punycode_domain_part.endswith('.') or '..' in punycode_domain_part:
        return False

    # Split domain into labels (e.g., "example.com" -> ["example", "com"])
    domain_labels = punycode_domain_part.split('.')

    # 2. Domain must have at least two labels (e.g., "example.com" is valid, "example" is not for public email).
    # This is a practical rule; single-label domains are generally not valid for public email delivery.
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
        # This regex strictly follows RFC 1035 for hostname labels.
        label_pattern = r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$"
        if not re.fullmatch(label_pattern, label):
            return False

    # 4. TLD (Top-Level Domain) validation
    # TLD is the last label. The `label_pattern` already ensures it's at least 1 character long
    # and follows naming rules (alphanumeric start/end, no consecutive hyphens, etc.).
    # The previous `len(tld) < 2` check is removed as it's overly restrictive for some technically valid TLDs
    # (e.g., single-character TLDs, though rare, are permitted by RFC 1035 for labels).

    return True