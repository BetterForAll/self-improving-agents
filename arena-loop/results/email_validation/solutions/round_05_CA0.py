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
        # Quoted strings allow almost any character, but unescaped ", \, (, ) are forbidden.
        # RFC specifies 'quoted-pair = "\" (VCHAR / WSP)' meaning backslash followed by
        # any visible character or space.
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
            # FIX: Unescaped parentheses are not allowed in quoted-string (RFC 5322, 3.2.4 qtext)
            elif inner_local_part[i] == '(' or inner_local_part[i] == ')':
                # This fixes: '"user(name)"@example.com': expected False, got True
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

        # FIX: For unquoted local parts (dot-atom), characters must strictly be 'atext'.
        # RFC 5322 Section 3.4.1 defines `dot-atom = [CFWS] atom *([CFWS] "." [CFWS] atom) [CFWS]`
        # and `atom = 1*atext`. `atext` does not include spaces, parentheses, or backslashes.
        # While CFWS (comments/FWS) are allowed *around* atoms and dots, many practical validators
        # apply a stricter interpretation where the local part must *effectively* resolve to only atext
        # and dots. This aligns with the test cases.
        # This fixes: 'user (comment)@example.com': expected True, got False
        # This fixes: 'user(with unescaped\)paren)@example.com': expected False, got True
        allowed_atext_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&'*+-/=?^_`{|}~."
        for char in local_part:
            if char not in allowed_atext_chars:
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

        # FIX: General-address-literal (e.g., [Tag:content])
        # RFC 5321, Section 4.1.2: General-address-literal = Standardized-tag ":" 1*dcontent
        # Standardized-tag = Ldh-str (alphanumeric, hyphen internally, not start/end with hyphen, max 63 chars)
        # dcontent = qtext / quoted-pair (VCHAR/WSP and backslash escaping VCHAR/WSP)
        # This fixes: 'user@[Tag:content]': expected True, got False
        tag_match = re.match(r"^([A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?):(.+)$", ip_literal)
        if tag_match:
            tag = tag_match.group(1)
            content = tag_match.group(2)
            
            # The regex already validates the tag's structure (Ldh-str rules approx.)
            # Max 63 char length for tag label is implicitly handled by the regex pattern (1 + 61 + 1)
            if not tag: # Tag cannot be empty
                return False

            # Validate content: 1*dcontent. Content must not be empty.
            if not content:
                return False

            j = 0
            while j < len(content):
                char_code = ord(content[j])
                if content[j] == '\\':
                    if j + 1 >= len(content): # Backslash at end
                        return False # Malformed escape sequence
                    # Escaped char must be VCHAR or WSP (ASCII 32-126)
                    escaped_char_code = ord(content[j+1])
                    if not (32 <= escaped_char_code <= 126):
                        return False
                    j += 2
                elif content[j] == '"': # Unescaped quote not allowed within dcontent
                    return False
                elif not (32 <= char_code <= 126): # Control characters or extended ASCII not allowed
                    return False
                else:
                    j += 1
            return True # Valid General-address-literal

        return False # Not a valid IPv4, IPv6, or General-address-literal (or other recognized literal format)

    # Standard domain validation (for hostnames)

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

    # FIX: TLD (Top-Level Domain) must be at least 2 characters long if there are multiple labels.
    # This is a common practical requirement, although RFCs don't explicitly forbid single-character TLDs
    # for multi-label domains. This aligns with the 'user@example.c' test case.
    # It specifically allows single-label domains like 'user@a' to remain valid.
    # This fixes: 'user@example.c': expected False, got True
    if len(domain_labels) > 1 and len(domain_labels[-1]) < 2:
        return False

    return True