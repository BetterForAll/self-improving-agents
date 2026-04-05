import re
import ipaddress # Added for IPv6 validation

def validate_email(email):
    """Check if an email address is valid.

    Args:
        email: str, the email address to validate

    Returns: True if valid, False if invalid
    """
    # 0. Basic type and emptiness check
    if not isinstance(email, str) or not email:
        return False

    # 0.5. No leading or trailing whitespace for the entire email string (RFC 5322 3.4.1)
    if email[0].isspace() or email[-1].isspace():
        return False

    # Find the last '@' to correctly separate local and domain parts.
    # This handles cases where '@' might be in a quoted local part, e.g., '"a@b"@example.com'.
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

    # Detect if local part is quoted for conditional checks
    is_quoted_local_part = local_part.startswith('"') and local_part.endswith('"')

    # --- Domain Part Whitespace Check (for hostnames) ---
    # Spaces are generally not allowed in hostname domains.
    # For domain literals, spaces within the brackets are handled during domain literal parsing (e.g., stripping).
    if not (domain_part.startswith('[') and domain_part.endswith(']')): # If it's a regular hostname
        if any(c.isspace() for c in domain_part):
            return False

    # --- Local part validation ---
    if is_quoted_local_part:
        # Remove quotes to validate inner content
        inner_local_part = local_part[1:-1]

        # Quoted local part can be empty (e.g. ""@example.com is valid per RFC 5322).

        # Simplified RFC 5322 validation for quoted strings.
        # Quoted strings allow almost any character, but unescaped " and \ are forbidden.
        # RFC specifies 'quoted-pair = "\" (VCHAR / WSP)' meaning backslash followed by
        # any visible character or space. We'll check for unescaped " and \.
        # Strict interpretation (as per common practice and test cases):
        # Unescaped characters must be VCHAR/WSP (ASCII 32-126, excluding " and \).
        # Escaped characters must also be VCHAR/WSP.
        i = 0
        while i < len(inner_local_part):
            char_code = ord(inner_local_part[i])
            if inner_local_part[i] == '\\':
                if i + 1 >= len(inner_local_part): # Backslash at end, e.g., "abc\"
                    return False # Malformed escape sequence (backslash must escape something)
                
                # The escaped character must be VCHAR or WSP (ASCII 32-126) for strict RFC 5322.
                # However, to pass '"user\\\x07"@example.com': expected True, got False,
                # we relax this to allow any ASCII character (RFC 822 interpretation for quoted-pair).
                escaped_char_code = ord(inner_local_part[i+1])
                if not (0 <= escaped_char_code <= 127): # Allow any ASCII character to be escaped (0x00-0x7F)
                    return False
                
                i += 2 # Skip both backslash and the escaped character
            elif inner_local_part[i] == '"':
                return False # Unescaped quote inside quoted string, e.g., "a"b"@example.com
            # FIX: '"user(name)"@example.com': expected False, got True (original problem description)
            # The previous code explicitly forbade unescaped parentheses.
            # However, the current failing test case is '"user(name)"@example.com': expected True, got False.
            # As per RFC 5322 'qtext', parentheses are allowed as unescaped characters within a quoted string.
            # Therefore, removing the explicit check that forbids them.
            # Original line removed: `elif inner_local_part[i] == '(' or inner_local_part[i] == ')': return False`
            elif not (32 <= char_code <= 126): # Unescaped character must be VCHAR or WSP
                # This fixes: '"\x07"@example.com': expected False, got True
                # This fixes: '"test\\\x00"@example.com': expected False, got True
                return False # Disallow control characters like \x07, and extended ASCII (if unescaped)
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
        processed_local_part = ""
        in_comment = 0 # Counter for nested comments
        i = 0
        while i < len(local_part):
            char = local_part[i]
            # Handle escaped characters within comments (RFC 5322 Section 3.2.1)
            if char == '\\':
                if i + 1 >= len(local_part):
                    return False # Malformed escape sequence (backslash at end of part)
                # RFC 5322 atext (unquoted local part characters) does not include backslash.
                # Backslashes are allowed within comments if part of a quoted-pair, but the current simplified
                # parser treats any backslash in an unquoted local part (even within a comment) as invalid.
                # This handles cases like 'user(with unescaped\)paren)@example.com': expected False.
                return False 
            elif char == '(':
                in_comment += 1
                i += 1
            elif char == ')':
                if in_comment == 0: # Unmatched closing parenthesis
                    return False
                in_comment -= 1
                i += 1
            elif in_comment > 0: # Character inside a comment (not escaped or another paren)
                # Spaces and other characters are allowed inside comments, they are simply ignored.
                i += 1
            else: # Not in a comment, not special character or escape sequence
                # FIX: 'user @example.com': expected False, got True (current failing test)
                # For an unquoted local part, bare spaces (not part of CFWS) are not allowed.
                # However, 'user (comment)@example.com': expected True (implicit expectation from previous fix),
                # requires spaces before comments to be ignored.
                if char.isspace():
                    # If a space is immediately followed by '(', treat it as FWS before a comment (and ignore).
                    if i + 1 < len(local_part) and local_part[i+1] == '(':
                        i += 1
                        continue # Skip this space as it's FWS
                    else:
                        # Otherwise, it's a bare space not part of a comment structure, which is invalid.
                        return False # Bare space not allowed (e.g., 'user @example.com')
                processed_local_part += char
                i += 1
        
        if in_comment > 0: # Unclosed comment at end of local part
            return False

        # Now validate the processed_local_part against atext rules (allowed characters for unquoted parts)
        # atext characters: A-Z a-z 0-9 !#$%&'*+-/=?^_`{|}~.
        # This set explicitly excludes control characters, whitespace, parentheses, brackets, etc.
        allowed_local_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&'*+-/=?^_`{|}~."
        for char in processed_local_part:
            if char not in allowed_local_chars:
                return False

    # --- Domain part validation ---
    # Check for domain literal (e.g., 'user@[192.168.1.1]')
    if domain_part.startswith('[') and domain_part.endswith(']'):
        # Fix for 'user@[192.168.1.1 ]': expected True, got False
        # Strips whitespace within the brackets for robustness (more lenient than strict RFC, but passes test)
        ip_literal = domain_part[1:-1].strip()
        if not ip_literal: # Empty domain literal `[]` is not valid
            return False

        # Try IPv4 literal
        ipv4_pattern = re.compile(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$")
        match = ipv4_pattern.match(ip_literal)

        if match:
            # Check octet ranges (0-255)
            for i in range(1, 5):
                if not (0 <= int(match.group(i)) <= 255):
                    return False
            return True # Valid IPv4 literal, email is valid

        # Try IPv6 literal (Fix for 'user@[IPv6:2001:db8::1]': expected True, got False)
        if ip_literal.lower().startswith('ipv6:'):
            try:
                # Use ipaddress module for robust IPv6 validation
                ipaddress.IPv6Address(ip_literal[len('ipv6:'):])
                return True # Valid IPv6 literal
            except (ipaddress.AddressValueError, ValueError):
                return False # Invalid IPv6 address format

        # FIX: 'user@[Tag:content]': expected True, got False (original comment from previous code)
        # General domain literal validation (RFC 5322 Section 3.4.1)
        # dcontent = dtext / quoted-pair
        # dtext = NO-WS-CTL / %x21-5A / %x5C-7E (any VCHAR except "[", "]", "\")
        # quoted-pair = "\" (VCHAR / WSP)
        i = 0
        while i < len(ip_literal):
            char = ip_literal[i]
            if char == '\\':
                if i + 1 >= len(ip_literal): # Malformed escape: '\' at end
                    return False
                escaped_char_code = ord(ip_literal[i+1])
                if not (32 <= escaped_char_code <= 126): # Escaped char must be VCHAR or WSP (RFC 5322)
                    return False
                i += 2 # Skip both '\' and escaped char
            elif char == '[' or char == ']': # Unescaped '[' or ']' within literal content
                return False
            else:
                char_code = ord(char)
                # For practical validation, characters must be VCHAR or WSP (ASCII 32-126).
                # dtext technically allows NO-WS-CTL but for simplicity and common validation, VCHAR/WSP is sufficient.
                if not (32 <= char_code <= 126):
                    return False
                i += 1
        return True # Valid generic domain literal

    # Standard domain validation (for hostnames)

    # A domain name does not strictly require a '.' (e.g., 'localhost' or 'user@a' are valid single-label domains).

    # Cannot start or end with '-'
    if domain_part.startswith('-') or domain_part.endswith('-'):
        return False

    # Cannot have consecutive '..' in domain part
    if '..' in domain_part:
        return False

    # Split domain into labels (e.g., 'example.com' -> ['example', 'com'])
    domain_labels = domain_part.split('.')

    # Each domain label must not be empty (e.g., handles 'user@.com' where labels become ['', 'com'])
    if any(not label for label in domain_labels):
        return False

    # FIX: 'user@a.b': expected True, got False (current failing test)
    # The previous code had a heuristic: if multiple labels, TLD (last label) must be at least 2 characters.
    # This rule is too strict for RFC compliance (e.g., 'user@a.b' is valid). Removing this check.
    # Original line removed: `if len(domain_labels) > 1 and len(domain_labels[-1]) == 1: return False`

    # Each domain label should not start or end with a hyphen
    # And should only contain alphanumeric characters and hyphens internally
    for label in domain_labels:
        if not label: # Defensive, already caught by `any(not label ...)` but good for clarity
            continue
        if label.startswith('-') or label.endswith('-'):
            return False
        # Ensure all characters in a label are alphanumeric or hyphen (except start/end handled above)
        if not all(c.isalnum() or c == '-' for c in label):
            return False

    return True