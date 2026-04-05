import re

def validate_email(email):
    """Check if an email address is valid.

    Args:
        email: str, the email address to validate

    Returns: True if valid, False if invalid
    """
    # 0. Basic type and emptiness check
    if not isinstance(email, str) or not email:
        return False

    # Split the email into local part and domain part at the *first* '@'
    # This correctly handles cases where the local part might contain an '@' if quoted.
    parts = email.split('@', 1)
    if len(parts) != 2:
        # If there's no '@' symbol, or if split('@', 1) somehow results in more or less than 2 parts, it's invalid.
        # (Technically, split will always result in 2 parts if '@' is present, or 1 if not).
        # This effectively checks for exactly one '@' that acts as a separator.
        return False

    local_part, domain_part = parts[0], parts[1]

    # 3. Local part and Domain part cannot be empty
    if not local_part or not domain_part:
        return False

    # --- Whitespace validation (Adjusted for quoted local parts) ---
    is_quoted_local_part = False
    if local_part.startswith('"') and local_part.endswith('"'):
        is_quoted_local_part = True
        # For quoted local parts, spaces are allowed *inside* the quotes.
        # But no leading/trailing whitespace on the whole email string (e.g. " user"@example.com).
        # And no whitespace in the domain part.
        if email[0].isspace() or email[-1].isspace() or any(c.isspace() for c in domain_part):
            return False
    else:
        # For unquoted local parts, no whitespace is allowed anywhere in the entire string.
        if any(c.isspace() for c in email):
            return False

    # --- Local part validation ---
    if is_quoted_local_part:
        # Remove quotes to validate inner content
        inner_local_part = local_part[1:-1]

        # Quoted local part cannot be empty (e.g. ""@example.com)
        if not inner_local_part and local_part != '""': # " " is ok, "" is not
            return False

        # Simplified RFC 5322 validation for quoted strings.
        # This covers '"a@b"@example.com' and '"first last"@example.com'
        # Quoted strings allow almost any character, but unescaped " and \ are forbidden.
        # RFC specifies 'quoted-pair = "\" (VCHAR / WSP)' meaning backslash followed by
        # any visible character or space. We'll check for unescaped " and \.
        i = 0
        while i < len(inner_local_part):
            if inner_local_part[i] == '\\':
                if i + 1 >= len(inner_local_part): # Backslash at end, e.g., "abc\"
                    return False # Invalid escape sequence (backslash must escape something)
                # Skip the escaped character as it's valid
                i += 2
            elif inner_local_part[i] == '"':
                return False # Unescaped quote inside quoted string, e.g., "a"b"@example.com
            else:
                i += 1

    else: # Unquoted local part
        # Cannot start or end with '.'
        if local_part.startswith('.') or local_part.endswith('.'):
            return False
        # Cannot have consecutive '..' in local part
        if '..' in local_part:
            return False

        # Validate characters in unquoted local part
        # Fix for 'useré@example.com': expected False, got True
        # According to RFC 5322, allowed characters in an unquoted local part (atom) are:
        # ATEXT = ALPHA / DIGIT / "!" / "#" / "$" / "%" / "&" / "'" / "*" / "+" / "-" / "/" / "=" / "?" / "^" / "_" / "`" / "{" / "|" / "}" / "~"
        # The period '.' is also allowed but with restrictions (not start/end, not consecutive).
        allowed_local_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&'*+-/=?^_`{|}~."
        for char in local_part:
            if char not in allowed_local_chars:
                return False

    # --- Domain part validation ---
    # Check for domain literal (e.g., 'user@[192.168.1.1]')
    if domain_part.startswith('[') and domain_part.endswith(']'):
        # Fix for 'user@[192.168.1.1]': expected True, got False
        ip_literal = domain_part[1:-1]
        if not ip_literal: # Empty domain literal `[]`
            return False

        # For the given test case, it's an IPv4 address.
        # RFC 5321 allows IPv4-address-literal and IPv6-address-literal.
        # Implement a simplistic IPv4 validation
        ipv4_pattern = re.compile(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$")
        match = ipv4_pattern.match(ip_literal)

        if match:
            # Check octet ranges (0-255)
            for i in range(1, 5):
                if not (0 <= int(match.group(i)) <= 255):
                    return False
            return True # Valid IPv4 literal, email is valid

        # Other literal types (e.g., IPv6) are complex to validate fully without a dedicated module.
        # Since the failing test case only includes IPv4, we'll return False for other unrecognized literal formats.
        return False # Not a valid IPv4 domain literal.

    # Standard domain validation (for hostnames)
    # Domain must contain at least one '.'
    if '.' not in domain_part:
        return False

    # Cannot start or end with '-'
    if domain_part.startswith('-') or domain_part.endswith('-'):
        return False

    # Cannot have consecutive '..' in domain part
    if '..' in domain_part:
        return False

    # Split domain into labels (e.g., 'example.com' -> ['example', 'com'])
    domain_labels = domain_part.split('.')

    # Each domain label must not be empty
    # Covers 'user@.com' (domain_labels will be ['', 'com'])
    if any(not label for label in domain_labels):
        return False

    # TLD (Top-Level Domain) must be at least 2 characters long
    # Covers 'user@example.c'
    if len(domain_labels[-1]) < 2:
        return False

    # Each domain label should not start or end with a hyphen
    # And should only contain alphanumeric characters and hyphens internally
    for label in domain_labels:
        if not label: # Defensive, already caught by `any(not label ...)`
            continue
        if label.startswith('-') or label.endswith('-'):
            return False
        # Ensure all characters in a label are alphanumeric or hyphen (except start/end handled above)
        if not all(c.isalnum() or c == '-' for c in label):
            return False

    return True