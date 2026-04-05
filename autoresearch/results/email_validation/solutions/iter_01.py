def validate_email(email):
    import re

    # 1. Basic structural checks
    # An email address must contain exactly one '@' symbol.
    if email.count('@') != 1:
        return False

    local_part, domain_part = email.split('@')

    # 2. Local Part validation
    # The local part cannot be empty.
    if not local_part:
        return False

    # The local part cannot start or end with a dot.
    # It also cannot contain consecutive dots.
    if local_part.startswith('.') or local_part.endswith('.') or '..' in local_part:
        return False

    # Validate characters in the local part.
    # This regex allows alphanumeric characters and a common set of special characters
    # (RFC 5322 section 3.4.1 for atom characters, excluding spaces and non-ASCII for simplicity).
    # The dot is included here, but its placement (start/end/consecutive) is checked above.
    # re.fullmatch ensures the entire string matches the pattern.
    if not re.fullmatch(r"[a-zA-Z0-9!#$%&'*+\-/=?^_`{|}~.]+", local_part):
        return False

    # 3. Domain Part validation
    # The domain part cannot be empty.
    if not domain_part:
        return False

    # The domain part must contain at least one dot to separate domain labels
    # (e.g., example.com, not just 'localhost').
    if '.' not in domain_part:
        return False

    # The domain part cannot start or end with a hyphen or a dot.
    if domain_part.startswith('-') or domain_part.endswith('-') or \
       domain_part.startswith('.') or domain_part.endswith('.'):
        return False

    # The domain part cannot contain consecutive dots.
    if '..' in domain_part:
        return False

    # Split the domain into labels and validate each label.
    labels = domain_part.split('.')

    # There must be at least two labels (e.g., "example.com" has two: "example" and "com").
    if len(labels) < 2:
        return False

    for label in labels:
        # Each label cannot be empty (e.g., due to "example..com", though '..' check catches this).
        if not label:
            return False

        # Each label cannot start or end with a hyphen.
        if label.startswith('-') or label.endswith('-'):
            return False

        # Each label must contain only alphanumeric characters and hyphens.
        if not re.fullmatch(r"[a-zA-Z0-9-]+", label):
            return False

    # 4. Top-Level Domain (TLD) validation
    tld = labels[-1]

    # The TLD must be at least 2 characters long.
    if len(tld) < 2:
        return False
    
    # TLD characters are already validated by the label check (alphanumeric and hyphens).
    # For practical purposes, this is usually sufficient, allowing for new gTLDs.

    return True