import re

def validate_email(email):
    """Check if an email address is valid.

    Args:
        email: str, the email address to validate

    Returns: True if valid, False if invalid
    """
    # 1. Check for leading/trailing whitespace
    if email.strip() != email:
        return False

    # The original step-by-step checks for local and domain parts are now
    # largely replaced or made redundant by a more comprehensive regular expression
    # for better RFC compliance and handling of edge cases.

    # Regex for an unquoted local part (dot-atom as per RFC 5322)
    # Allows alphanumeric characters, and specific symbols: !#$%&'*+-/=?^_`{|}~
    # Dots are allowed, but not at the start/end or consecutively, which this pattern ensures.
    dot_atom_pattern = r"[a-zA-Z0-9!#$%&'*+-/=?^_`{|}~]+(?:\.[a-zA-Z0-9!#$%&'*+-/=?^_`{|}~]+)*"
    
    # Regex for a quoted-string local part (as per RFC 5322)
    # Allows almost any character inside quotes, except an unescaped double quote (") or backslash (\).
    # `[^"\\]` matches any character that is not a double quote or a backslash.
    # `\\.` matches a backslash followed by any character (to allow escaped characters like \" or \\).
    # `(?:...)` is a non-capturing group. `*` allows zero or more occurrences of the content inside quotes.
    quoted_string_pattern = r'"(?:[^"\\]|\\.)*"'

    # Combined local part pattern: either a dot-atom OR a quoted-string.
    local_part_full_pattern = f"(?:{dot_atom_pattern}|{quoted_string_pattern})"

    # Regex for a single domain label (e.g., "example", "com", "sub-domain")
    # As per RFC 1035/1123, labels must start and end with an alphanumeric character.
    # They can contain alphanumeric characters and hyphens in between.
    # Maximum length of 63 characters per label is standard, but the regex enforces
    # start/end chars and hyphen content for up to 61 middle chars.
    domain_label_pattern = r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    
    # Regex for the Top-Level Domain (TLD)
    # TLDs are typically at least two alphabetic characters (e.g., "com", "org", "co.uk").
    # This pattern excludes purely numeric TLDs (e.g., '123' in an IP address),
    # which fixes the 'user@192.168.1.123' failure.
    tld_pattern = r"[a-zA-Z]{2,}"

    # Full domain pattern: one or more labels separated by dots, ending with a TLD.
    # This structure inherently validates against empty labels, leading/trailing dots,
    # and consecutive dots in the domain name.
    domain_full_pattern = f"(?:{domain_label_pattern}\\.)+{tld_pattern}"

    # Combine the local part and domain part with the '@' separator.
    # The `^` and `$` anchors ensure that the entire email string matches the pattern.
    full_email_pattern = fr"^{local_part_full_pattern}@{domain_full_pattern}$"

    # Attempt to match the entire email string against the comprehensive pattern.
    match = re.fullmatch(full_email_pattern, email)

    if not match:
        return False

    # Extract local and domain parts after successful regex match.
    # We use split('@', 1) to ensure we split only on the first (unquoted) '@',
    # which the regex inherently validates as the domain separator.
    local_part, domain_part = email.split('@', 1)

    # 4. Local part length validation
    # RFC 5322 section 3.4.1 states that the local-part SHOULD NOT exceed 64 characters.
    # This fixes the 'aaaaaaaa... @example.com' failure.
    if len(local_part) > 64:
        return False

    # 5. Domain part length validation
    # RFC 1035 section 2.3.4 limits domain names to 255 characters.
    if len(domain_part) > 255:
        return False

    # 6. Top-Level Domain (TLD) specific checks
    # The TLD is the last part of the domain after the last dot.
    domain_labels = domain_part.split('.')
    tld = domain_labels[-1]
    
    # Check for reserved or disallowed TLDs.
    # '.localhost' is a special-use domain name (RFC 2606) and is generally
    # considered invalid for public email addresses.
    # This fixes the 'user@example.localhost' failure.
    if tld.lower() == 'localhost':
        return False

    # All checks passed, the email address is considered valid.
    return True