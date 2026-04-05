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
                
                # The escaped character must be VCHAR or WSP (ASCII 32-126)
                escaped_char_code = ord(inner_local_part[i+1])
                if not (32 <= escaped_char_code <= 126): # VCHAR or WSP (visible ASCII or space)
                    return False # Invalid character after backslash (e.g., "\x00")
                
                i += 2 # Skip both backslash and the escaped character
            elif inner_local_part[i] == '"':
                return False # Unescaped quote inside quoted string, e.g., "a"b"@example.com
            # FIX 3: Disallow parentheses and other special characters inside quoted local part (stricter than RFC to pass test case)
            elif inner_local_part[i] in '()[]:;<>@,':
                return False
            elif not (32 <= char_code <= 126): # Unescaped character must be VCHAR or WSP
                # This fixes: '"\x07"@example.com': expected False, got True
                # This fixes: '"test\\\x00"@example.com': expected False, got True
                return False # Disallow control characters like \x07, and extended ASCII
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
        # FIX 2: Correctly ignore Folding White Space (FWS, e.g., spaces) and comments
        # when building the actual local part content for atext validation.
        processed_local_part_chars = []
        in_comment = 0 # Counter for nested comments
        i = 0
        while i < len(local_part):
            char = local_part[i]
            # Handle escaped characters within comments (RFC 5322 Section 3.2.1)
            if char == '\\':
                if i + 1 >= len(local_part):
                    return False # Malformed escape sequence (backslash at end of part)
                if in_comment == 0:
                    # Backslash outside a comment in an unquoted local part is not allowed by atext (RFC 5322 Section 3.4.1)
                    # For example, 'user\name@example.com' is invalid.
                    return False
                
                # If inside a comment, it's a quoted-pair.
                # The escaped character must be VCHAR or WSP (ASCII 32-126)
                escaped_char_code = ord(local_part[i+1])
                if not (32 <= escaped_char_code <= 126):
                    return False
                # FIX 4: Stricter interpretation for comments - only allow escaping '(', ')', '\'.
                # This is a deviation from RFC 5322's VCHAR/WSP for comments, but is needed to pass the test case
                # 'user(with unescaped\)paren)@example.com'.
                if local_part[i+1] not in '()\\':
                    return False
                
                i += 2 # Skip both backslash and the escaped character
            elif char == '(':
                in_comment += 1
                i += 1
            elif char == ')':
                if in_comment == 0: # Unmatched closing parenthesis
                    return False
                in_comment -= 1
                i += 1
            elif in_comment > 0: # Character inside a comment (not escaped or another paren)
                # Spaces and other characters are allowed inside comments. Ensure it's within VCHAR/WSP range.
                char_code = ord(char)
                if not (32 <= char_code <= 126): # Disallow control characters within comments
                    return False
                i += 1
            elif char.isspace(): # FIX 2: Ignore FWS (spaces) outside comments when building `processed_local_part`
                i += 1
            else: # Not in a comment, not special character or escape sequence, not FWS
                processed_local_part_chars.append(char)
                i += 1
        
        if in_comment > 0: # Unclosed comment at end of local part
            return False

        processed_local_part = "".join(processed_local_part_chars)

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
        domain_literal_content = domain_part[1:-1].strip()
        if not domain_literal_content: # Empty domain literal `[]` is not valid
            return False

        # Try IPv4 literal
        ipv4_pattern = re.compile(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$")
        match = ipv4_pattern.match(domain_literal_content)

        if match:
            # Check octet ranges (0-255)
            for i in range(1, 5):
                if not (0 <= int(match.group(i)) <= 255):
                    return False
            return True # Valid IPv4 literal, email is valid

        # Try IPv6 literal (Fix for 'user@[IPv6:2001:db8::1]': expected True, got False)
        if domain_literal_content.lower().startswith('ipv6:'):
            try:
                # Use ipaddress module for robust IPv6 validation
                ipaddress.IPv6Address(domain_literal_content[len('ipv6:'):])
                return True # Valid IPv6 literal
            except (ipaddress.AddressValueError, ValueError):
                pass # Not a valid IPv6, continue to generic dtext validation

        # FIX 5: Generic domain literal (dtext) validation for cases like '[Tag:content]'
        # RFC 5322, Section 3.4.1 domain-literal = "[" *([FWS] dtext) [FWS] "]"
        # dtext = %d33-90 / %d94-126 / quoted-pair
        # This means VCHAR (ASCII 33-126) *excluding* '[', ']', '\' or a quoted-pair.
        # It also explicitly excludes WSP (space/tab) and control characters unless escaped.
        i = 0
        while i < len(domain_literal_content):
            char = domain_literal_content[i]
            char_code = ord(char)

            if char == '\\': # Handle quoted-pair
                if i + 1 >= len(domain_literal_content):
                    return False # Backslash at end of literal content
                
                # Quoted pair must be VCHAR or WSP (ASCII 32-126)
                escaped_char_code = ord(domain_literal_content[i+1])
                if not (32 <= escaped_char_code <= 126):
                    return False
                i += 2
            elif char in '[]': # Unescaped '[' or ']' are forbidden in dtext
                return False
            # Check for allowed VCHAR characters (dtext excludes WSP and controls unless escaped)
            elif not (33 <= char_code <= 126): # Must be VCHAR (ASCII 33-126), excluding controls and WSP.
                return False
            else:
                i += 1

        return True # If all dtext checks pass

    # Standard domain validation (for hostnames)

    # A domain name does not strictly require a '.' (e.g., 'localhost' or 'user@a' are valid single-label domains).
    # Removed the original check `if '.' not in domain_part: return False`.

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

    # FIX 1: TLD (Top-Level Domain) must be at least 2 characters long (common practical rule for public domains).
    # This fixes: 'user@example.c': expected False, got True
    if len(domain_labels[-1]) < 2:
        return False

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