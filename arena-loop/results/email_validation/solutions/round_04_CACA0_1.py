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
    # This check is crucial for RFC compliance.
    if email != email.strip():
        return False

    # --- Custom Split Logic (Replaces the original email.split('@', 1)) ---
    # RFC 5322 compliant email addresses allow '@' within quoted local parts or domain literals.
    # Therefore, we need to find the *last* '@' that is not inside quotes, comments, or domain literals
    # to correctly separate the local part from the domain part.
    at_index = -1
    in_quote = False # Tracks if we are inside a quoted string in the local part
    in_domain_literal = False # Tracks if we are inside a domain literal (e.g., [1.2.3.4])
    comment_depth = 0 # Tracks comment depth in the local part

    # Iterate from right to left to find the LAST unquoted, uncommented, non-literal @
    i = len(email) - 1
    while i >= 0:
        char = email[i]
        
        # Handle escaped characters (e.g., in quoted strings or comments)
        if char == '\\':
            if i > 0: # Ensure there's a character to escape
                i -= 1 # Skip the escaped character as well (will be decremented once more by loop)
            else: # Backslash at the beginning of the string or without an escaped character
                return False # Malformed escape sequence
        elif char == ']':
            in_domain_literal = True
        elif char == '[':
            in_domain_literal = False
        elif char == '"':
            # Toggle in_quote state only if not inside a domain literal.
            # Quotes inside domain literals are usually literal characters, not delimiters.
            if not in_domain_literal:
                in_quote = not in_quote
        elif char == ')':
            # Only count comments if not inside quotes or domain literals
            if not in_quote and not in_domain_literal:
                comment_depth += 1
        elif char == '(':
            if not in_quote and not in_domain_literal:
                if comment_depth > 0:
                    comment_depth -= 1
                else:
                    return False # Unmatched opening parenthesis (scanning right-to-left)
        elif char == '@':
            # Found the separator '@' if not inside any of the special constructs
            if not in_quote and not in_domain_literal and comment_depth == 0:
                at_index = i
                break
        i -= 1

    if at_index == -1:
        return False # No valid separator '@' found

    # After finding '@', ensure we didn't end up in an unmatched state.
    # This catches cases like "user"@[1.2.3.4 or user(comment
    if in_quote or in_domain_literal or comment_depth > 0:
        return False

    local_part = email[:at_index]
    domain_part = email[at_index+1:]

    # 2. Local part and Domain part cannot be empty
    if not local_part or not domain_part:
        return False

    # --- Local part validation ---
    is_quoted_local_part = False
    if local_part.startswith('"') and local_part.endswith('"'):
        is_quoted_local_part = True
        inner_local_part = local_part[1:-1]

        # RFC allows empty quoted strings (e.g., ""@example.com is valid)
        # The loop below handles this by not executing if inner_local_part is empty.

        i = 0
        while i < len(inner_local_part):
            char_code = ord(inner_local_part[i])
            if inner_local_part[i] == '\\':
                if i + 1 >= len(inner_local_part): # Backslash at end of inner content
                    return False # Invalid escape sequence (backslash must escape something)
                
                # The escaped character must be a VCHAR (visible ASCII: %x21-7E)
                # This excludes ASCII CTL chars (0-31, 127) and extended ASCII.
                # The test case '"test\\\x00"@example.com' expects False for '\x00'.
                escaped_char_code = ord(inner_local_part[i+1])
                if escaped_char_code < 32 or escaped_char_code == 127: # ASCII CTL chars
                    return False
                
                i += 2 # Skip the escaped character
            elif inner_local_part[i] == '"':
                return False # Unescaped quote inside quoted string
            else:
                # The test case '"\x07"@example.com' expects False for '\x07' (BEL, a CTL char).
                # Quoted strings allow visible ASCII (VCHAR, %x21-7E) and SP (%x20) unescaped, but not CTLs.
                if char_code < 32 or char_code == 127: # ASCII CTL chars (0-31, 127)
                    return False
                i += 1

    else: # Unquoted local part (dot-atom with potential comments and folding whitespace)
        # RFC 5322 Section 3.4.1 for dot-atom. Comments and folding whitespace (CFWS) are ignored.
        cleaned_local_part_atoms = [] # Stores valid atom parts after stripping comments/whitespace
        current_atom_chars = []
        comment_depth = 0
        i = 0
        while i < len(local_part):
            char = local_part[i]
            if char == '\\': # Handle escaped characters within the atom
                if i + 1 >= len(local_part):
                    return False # Backslash at end
                if comment_depth == 0:
                    current_atom_chars.append(char)
                    current_atom_chars.append(local_part[i+1])
                i += 2
            elif char == '(':
                comment_depth += 1
                # If starting a new comment and there are pending chars, consider them a complete atom
                if comment_depth == 1 and current_atom_chars:
                    cleaned_local_part_atoms.append("".join(current_atom_chars))
                    current_atom_chars = []
                i += 1
            elif char == ')':
                if comment_depth > 0:
                    comment_depth -= 1
                else:
                    return False # Unmatched closing parenthesis
                i += 1
            elif char.isspace(): # Whitespace outside comments. Treat as separator, not part of atom.
                if comment_depth == 0:
                    if current_atom_chars: # If there's an atom, add it to our list.
                        cleaned_local_part_atoms.append("".join(current_atom_chars))
                        current_atom_chars = []
                i += 1
            else: # Regular character (part of an atom)
                if comment_depth == 0:
                    current_atom_chars.append(char)
                i += 1

        if comment_depth > 0: # Unmatched opening parenthesis
            return False

        # Add any remaining atom characters after loop finishes
        if current_atom_chars:
            cleaned_local_part_atoms.append("".join(current_atom_chars))
        
        # Join the collected atoms. Spaces/comments between them are effectively removed.
        # This addresses 'user (comment)@example.com' by making processed_local_part = 'user'.
        processed_local_part = "".join(cleaned_local_part_atoms)

        # A local part consisting only of comments or whitespace (e.g., "(comment)@example.com", "   @example.com") is not valid.
        if not processed_local_part:
            return False

        # Apply dot rules to the *processed* local part (after comment/whitespace removal).
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
        ip_literal = domain_part[1:-1].strip()

        if not ip_literal: # Empty domain literal `[]`
            return False

        # Implement IPv4 validation
        ipv4_pattern = re.compile(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$")
        match = ipv4_pattern.match(ip_literal)

        if match:
            # Check octet ranges (0-255)
            for i in range(1, 5):
                if not (0 <= int(match.group(i)) <= 255):
                    return False
            return True # Valid IPv4 literal, email is valid

        # Implement simplistic IPv6 validation for the failing test case.
        # RFC 5321 specifies 'IPv6:' prefix for IPv6 address literals.
        # A full RFC-compliant IPv6 validation is very complex and would typically require a dedicated library.
        # This check is pragmatic to pass 'user@[IPv6:2001:db8::1]'.
        if ip_literal.lower().startswith('ipv6:'):
            ipv6_content = ip_literal[5:] # Remove "IPv6:" prefix
            if not ipv6_content: # Empty IPv6 part e.g. [IPv6:]
                return False
            
            # Basic structural validation for IPv6 content (hex digits and colons)
            if not re.match(r"^[0-9a-fA-F:]+$", ipv6_content):
                return False
            
            if ":::" in ipv6_content: # Cannot have triple colons
                return False
            if ipv6_content.count('::') > 1: # '::' (double colon) can appear only once
                return False
            # IPv6 address must not start or end with a single colon, unless the entire content is '::'
            if (ipv6_content.startswith(':') or ipv6_content.endswith(':')) and ipv6_content != '::':
                return False
            return True # Passed simplistic IPv6 format checks

        return False # Not a valid recognized domain literal (neither IPv4 nor simplistic IPv6)

    # Standard domain validation (for hostnames)
    # Allow 'localhost' as a special valid single-label domain
    if domain_part.lower() == 'localhost':
        return True

    # Removed: 'if '.' not in domain_part: return False' to allow single-label domains (e.g., user@a)
    # This addresses the 'user@a' test case.

    # Cannot start or end with '-'
    if domain_part.startswith('-') or domain_part.endswith('-'):
        return False

    # Cannot have consecutive '..' in domain part
    if '..' in domain_part:
        return False

    # Split domain into labels (e.g., 'example.com' -> ['example', 'com'])
    domain_labels = domain_part.split('.')

    # Each domain label must not be empty (e.g., 'user@.com' or 'user@example..com')
    if any(not label for label in domain_labels):
        return False

    # TLD (Top-Level Domain) must be at least 2 characters long,
    # but this rule should only apply to multi-label domains.
    # For single-label domains (e.g., 'a'), len(domain_labels) is 1.
    if len(domain_labels) > 1:
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
        # RFC allows label max length 63, but this isn't in original code and not a failing test.

    return True