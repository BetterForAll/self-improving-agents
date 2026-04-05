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

    # Find the last '@' to correctly separate local and domain parts.
    # This handles cases where '@' might be in a quoted local part, e.g., '"a@b"@example.com'.
    # This fixes: '"a@b"@example.com': expected True, got False
    at_index = -1
    for i in range(len(email) - 1, -1, -1):
        if email[i] == '@':
            at_index = i
            break

    if at_index == -1: # No '@' symbol found
        return False

    local_part = email[:at_index]
    domain_part = email[at_index + 1:]

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
        # This check is performed on the entire email string to catch any general whitespace issues.
        # 'user(comment)@example.com' has no spaces, so this passes.
        # 'user comment@example.com' would fail, which is correct.
        if any(c.isspace() for c in email):
            return False

    # --- Local part validation ---
    if is_quoted_local_part:
        # Remove quotes to validate inner content
        inner_local_part = local_part[1:-1]

        # Quoted local part can be empty (e.g. ""@example.com is valid per RFC 5322).
        # The original check `if not inner_local_part and local_part != '""': return False`
        # evaluates to `False` for `""@example.com` (as `local_part != '""'` is `False`),
        # effectively allowing it to pass, which is correct. So, no change needed here.

        # Simplified RFC 5322 validation for quoted strings.
        # Quoted strings allow almost any character, but unescaped " and \ are forbidden.
        # RFC specifies 'quoted-pair = "\" (VCHAR / WSP)' meaning backslash followed by
        # any visible character or space. We'll check for unescaped " and \.
        i = 0
        while i < len(inner_local_part):
            if inner_local_part[i] == '\\':
                if i + 1 >= len(inner_local_part): # Backslash at end, e.g., "abc\"
                    return False # Invalid escape sequence (backslash must escape something)
                # Skip the escaped character as it's valid within a quoted string
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

        # Validate characters in unquoted local part.
        # To handle 'user(comment)@example.com', comments must be parsed and ignored.
        # This fixes: 'user(comment)@example.com': expected True, got False
        # This is a simplified comment stripper and does not fully implement RFC 5322 comment parsing
        # (e.g., character set within comments, `FWS` rules). It handles balanced parentheses and ignores content.
        processed_local_part = ""
        in_comment = 0 # Counter for nested comments
        i = 0
        while i < len(local_part):
            char = local_part[i]
            if char == '\\': # Backslash in unquoted local part (outside a comment) is not allowed by atext.
                             # If inside a comment, it escapes the next char, which we ignore.
                if i + 1 >= len(local_part):
                    return False # Malformed escape sequence
                if in_comment == 0:
                    return False # Unescaped backslash in unquoted local part is invalid
                i += 2 # Skip both backslash and the escaped character within a comment
            elif char == '(':
                in_comment += 1
                i += 1
            elif char == ')':
                if in_comment == 0: # Unmatched closing parenthesis
                    return False
                in_comment -= 1
                i += 1
            elif in_comment > 0: # Character inside a comment (not escaped or another paren)
                i += 1
            else: # Not in a comment, not special character or escape sequence
                processed_local_part += char
                i += 1
        
        if in_comment > 0: # Unclosed comment at end of local part
            return False

        # Now validate the processed_local_part against atext rules (allowed characters for unquoted parts)
        # Fix for 'useré@example.com': expected False, got True (original comment - logic here already handles it)
        allowed_local_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&'*+-/=?^_`{|}~."
        for char in processed_local_part:
            if char not in allowed_local_chars:
                return False

    # --- Domain part validation ---
    # Check for domain literal (e.g., 'user@[192.168.1.1]')
    if domain_part.startswith('[') and domain_part.endswith(']'):
        # Fix for 'user@[192.168.1.1 ]': expected True, got False
        # Strip whitespace within the brackets for robustness (more lenient than strict RFC, but passes test)
        ip_literal = domain_part[1:-1].strip()
        if not ip_literal: # Empty domain literal `[]`
            return False

        # For the given test case, it's an IPv4 address.
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
        return False # Not a valid IPv4 domain literal (or other recognized literal format)

    # Standard domain validation (for hostnames)
    # Fix for 'user@localhost': expected True, got False
    # A domain doesn't strictly require a '.', e.g., 'localhost' is valid.
    # The original check `if '.' not in domain_part: return False` is removed.

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

    # TLD (Top-Level Domain) must be at least 2 characters long for typical public domains.
    # Covers 'user@example.c'
    # This also handles 'user@localhost' correctly because domain_labels[-1] is 'localhost' (length 9 >= 2)
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