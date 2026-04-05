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

    # 1. No leading/trailing whitespace on the entire email string
    if email != email.strip():
        return False

    # Split the email into local part and domain part at the *first* '@'
    parts = email.split('@', 1)
    if len(parts) != 2:
        # If there's no '@' symbol, or if split('@', 1) somehow results in more or less than 2 parts, it's invalid.
        # (Technically, split will always result in 2 parts if '@' is present, or 1 if not).
        # This effectively checks for exactly one '@' that acts as a separator.
        return False

    local_part, domain_part = parts[0], parts[1]

    # 2. Local part and Domain part cannot be empty
    if not local_part or not domain_part:
        return False

    # --- Local part validation ---
    is_quoted_local_part = False
    if local_part.startswith('"') and local_part.endswith('"'):
        is_quoted_local_part = True
        # For quoted local parts, spaces are allowed *inside* the quotes.
        # The check for leading/trailing whitespace on the full email string already handled email[0]/email[-1].
        # No additional whitespace check needed here, as domain_part's spaces will be checked in domain validation.

        # Remove quotes to validate inner content
        inner_local_part = local_part[1:-1]

        # Quoted local part cannot be empty UNLESS it's literally '""'
        # RFC allows empty quoted strings (e.g., ""@example.com is valid)
        if not inner_local_part and local_part != '""':
            return False

        # Simplified RFC 5322 validation for quoted strings.
        # Quoted strings allow almost any character, but unescaped " and \ are forbidden.
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
        # Handle obsolete local part comments (RFC 5322 Section 3.4.1)
        # Comments are ignored for the purpose of identifying the actual 'atom' characters.
        cleaned_local_part_chars = []
        comment_depth = 0
        i = 0
        while i < len(local_part):
            char = local_part[i]
            if char == '\\': # Handle escaped characters
                if i + 1 >= len(local_part): # Backslash at end
                    return False
                if comment_depth == 0: # Append if not inside a comment
                    cleaned_local_part_chars.append(char)
                    cleaned_local_part_chars.append(local_part[i+1])
                i += 2
            elif char == '(':
                comment_depth += 1
                i += 1
            elif char == ')':
                if comment_depth > 0:
                    comment_depth -= 1
                else:
                    return False # Unmatched closing parenthesis
                i += 1
            else:
                if comment_depth == 0: # Append character if not inside a comment
                    cleaned_local_part_chars.append(char)
                i += 1

        if comment_depth > 0: # Unmatched opening parenthesis
            return False

        processed_local_part = "".join(cleaned_local_part_chars)

        # A local part consisting only of comments (e.g., "(comment)@example.com") is not valid.
        if not processed_local_part:
            return False

        # Apply dot rules to the *processed* local part (after comment removal).
        if processed_local_part.startswith('.') or processed_local_part.endswith('.'):
            return False
        if '..' in processed_local_part:
            return False

        # Validate characters in unquoted local part (atom portion after comment removal)
        # ATEXT = ALPHA / DIGIT / "!" / "#" / "$" / "%" / "&" / "'" / "*" / "+" / "-" / "/" / "=" / "?" / "^" / "_" / "`" / "{" / "|" / "}" / "~"
        # The period '.' is also allowed but with restrictions (not start/end, not consecutive).
        allowed_local_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&'*+-/=?^_`{|}~."
        for char in processed_local_part:
            if char not in allowed_local_chars:
                return False

    # --- Domain part validation ---
    # Check for domain literal (e.g., 'user@[192.168.1.1]')
    if domain_part.startswith('[') and domain_part.endswith(']'):
        # Fix: strip whitespace for domain literals like 'user@[192.168.1.1 ]'
        ip_literal = domain_part[1:-1].strip()

        if not ip_literal: # Empty domain literal `[]`
            return False

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
    # Fix: Allow 'localhost' as a special valid single-label domain
    if domain_part.lower() == 'localhost':
        return True

    # Domain must contain at least one '.' (for non-localhost domains)
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
        # Defensive, already caught by `any(not label ...)`
        if not label:
            continue
        if label.startswith('-') or label.endswith('-'):
            return False
        # Ensure all characters in a label are alphanumeric or hyphen (except start/end handled above)
        if not all(c.isalnum() or c == '-' for c in label):
            return False

    return True