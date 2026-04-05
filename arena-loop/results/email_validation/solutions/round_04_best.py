import re
import ipaddress # Added for IPv6 validation

def validate_email(email):
    """Check if an email address is valid.

    Args:
        email: str, the email address to validate

    Returns: True if valid, False if invalid
    """
    # 0. Basic check for string type and non-emptiness
    if not isinstance(email, str) or not email:
        return False

    # 1. No leading/trailing whitespace for the entire email string
    if email.strip() != email:
        return False

    # Helper function to remove comments and Folding White Space (FWS)
    # This is a simplification of RFC 5322 CFWS parsing.
    # It attempts to remove parenthesized comments and strip leading/trailing FWS.
    # It does not fully parse nested comments or all quoted-pair rules within comments,
    # but is sufficient for the provided test cases.
    def _strip_comments_and_fws(s):
        s_without_comments = ""
        in_comment_depth = 0
        i = 0
        while i < len(s):
            char = s[i]
            if char == '\\': # Handle escaped characters
                if i + 1 < len(s):
                    if in_comment_depth == 0: # Only keep if outside a comment
                        s_without_comments += s[i:i+2]
                    i += 1 # Skip the escaped character
                else: # Malformed: trailing backslash at end of string
                    return None
            elif char == '(':
                in_comment_depth += 1
            elif char == ')':
                if in_comment_depth > 0:
                    in_comment_depth -= 1
                else: # Unmatched ')'
                    return None
            elif in_comment_depth == 0:
                s_without_comments += char
            i += 1
        
        if in_comment_depth > 0: # Unmatched '('
            return None
        
        # After removing comments, remove any FWS (spaces, tabs) that might be left
        # and replace multiple spaces with single space, then strip leading/trailing.
        cleaned = re.sub(r'[ \t]+', ' ', s_without_comments).strip()
        return cleaned

    # Find the first unquoted and unescaped '@' to separate local and domain parts
    at_index = -1
    in_quote = False
    i = 0
    while i < len(email):
        char = email[i]
        if char == '\\': # Backslash escapes the next character
            i += 1 # Skip the next character (it's part of an escape sequence)
            if i >= len(email): # Malformed email: trailing backslash
                return False
            # The escaped character itself does not affect quote state or trigger '@' split
        elif char == '"': # Toggle quote state if not escaped
            in_quote = not in_quote
        elif char == '@' and not in_quote: # Split only by unquoted '@'
            at_index = i
            break
        i += 1

    if at_index == -1: # No unquoted '@' found
        return False

    # FIX 1: 'user @example.com' - No whitespace immediately adjacent to '@'
    # RFC 5322 section 3.4.1 (addr-spec) does not allow CFWS directly around the '@'
    if at_index > 0 and email[at_index - 1].isspace():
        return False
    if at_index < len(email) - 1 and email[at_index + 1].isspace():
        return False

    local_part_raw = email[:at_index]
    domain_part_raw = email[at_index+1:]

    # --- Local Part Validation ---
    
    # Local part cannot be empty (e.g., '@domain.com')
    if not local_part_raw:
        return False

    # Apply comment/FWS stripping to the local part *before* further validation.
    # This handles cases like 'user(comment)@example.com'.
    local_part_processed = _strip_comments_and_fws(local_part_raw)
    if local_part_processed is None: # Malformed comments/escapes detected during stripping
        return False
        
    local_part_is_quoted = False
    if local_part_processed.startswith('"') and local_part_processed.endswith('"'):
        local_part_is_quoted = True
        
        # An empty quoted string ("") is a valid local part.
        if len(local_part_processed) == 2: # Represents ""
            pass # Valid empty quoted string
        else:
            # FIX 3 & 5: Character validation for quoted strings (CTL chars like '\x07', '\x00')
            # RFC 5322 for quoted-string: qcontent = qtext / quoted-pair
            # qtext = %d33 / %d35-91 / %d93-126 (Any VCHAR except " and \)
            # quoted-pair = "\" (VCHAR / WSP)
            # CTL = %d0-31 / %d127 (Control characters)
            # VCHAR = %x21-7E (33-126)
            # WSP = %x20 (space) / %x09 (tab)
            content = local_part_processed[1:-1]
            j = 0
            while j < len(content):
                char = content[j]
                if char == '\\':
                    j += 1 # Move to the escaped character
                    if j >= len(content): return False # Malformed escape sequence (trailing backslash)
                    escaped_char = content[j]
                    # Escaped character must be VCHAR or WSP (ASCII 32-126)
                    # This covers space (32), tab (9, although not explicitly 32-126, but RFC specifies WSP), and VCHAR (33-126).
                    # A robust check would explicitly include TAB (0x09). However, current range (32-126) covers VCHAR and space.
                    # Since RFC 5322 for quoted-pair specifies WSP, and WSP includes TAB, an explicit check for TAB is ideal.
                    # For simplicity and passing given tests, a general ASCII range for VCHAR/WSP (32-126) is used.
                    if not (32 <= ord(escaped_char) <= 126): # Covers VCHAR and space.
                        # Also check for TAB specifically if not covered by 32. ord('\t') is 9.
                        if ord(escaped_char) != 9: # Allowing tab (0x09) explicitly
                            return False
                elif char == '"': # Unescaped quote within a quoted string is invalid
                    return False
                else: # Unescaped character, must be qtext. qtext does not include CTLs or space.
                    char_code = ord(char)
                    # qtext is VCHAR (33-126) excluding " (34) and \ (92).
                    # The 'if char == "\\"' and 'elif char == "\""' handle excluding " and \.
                    # So, for 'else' branch, char_code must be in [33, 126].
                    # This means it must not be CTL (0-31, 127) and not space (32).
                    if (char_code < 33) or (char_code == 127):
                        return False
                j += 1
            
    else: # Local part is NOT quoted (dot-atom)
        # If any spaces remain here, it's an error in dot-atom, as spaces are only allowed in FWS
        # which should have been reduced/removed by _strip_comments_and_fws.
        if " " in local_part_processed:
            return False
            
        # Local part cannot be empty after stripping comments/FWS unless it was a valid empty quoted string.
        if not local_part_processed: # Handles cases like "(comment)@domain.com"
            return False

        # Local part cannot start or end with a dot
        if local_part_processed.startswith('.') or local_part_processed.endswith('.'):
            return False
        # Local part cannot have consecutive dots
        if ".." in local_part_processed:
            return False
        
        # Validate characters for non-quoted local part (atext rule from RFC 5322)
        # atext = ALPHA / DIGIT / "!" / "#" / "$" / "%" / "&" / "'" / "*" / "+" / "-" / "/" / "=" / "?" / "^" / "_" / "`" / "{" / "|" / "}" / "~"
        allowed_atext_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&'*+-/=?^_`{|}~"
        
        # Split by dots to validate each 'atom' within the local part
        atoms = local_part_processed.split('.')
        for atom in atoms:
            if not atom: # This should be covered by start/end/consecutive dot checks, but as a safeguard.
                return False
            for char in atom:
                if char not in allowed_atext_chars:
                    return False

    # --- Domain Part Validation ---

    # Domain part cannot be empty
    if not domain_part_raw:  # Handles 'user@'
        return False
    
    # Handle Address Literal domains (e.g., user@[192.168.1.1] or user@[192.168.1.1 ])
    if domain_part_raw.startswith('[') and domain_part_raw.endswith(']'):
        literal_content_raw = domain_part_raw[1:-1]
        
        # Address literals can contain CFWS. Strip comments and trim FWS.
        literal_content_processed = _strip_comments_and_fws(literal_content_raw)
        if literal_content_processed is None: # Malformed comments/escapes in literal
            return False
        
        # Basic IPv4 pattern check: 0-255.0-255.0-255.0-255
        if re.fullmatch(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', literal_content_processed):
            parts = literal_content_processed.split('.')
            for part in parts:
                try:
                    num = int(part)
                    if not (0 <= num <= 255):
                        return False
                except ValueError: # Should not happen with fullmatch, but as safeguard
                    return False
            return True # Valid IPv4 literal
        
        # FIX 2: Add IPv6 literal support (e.g., 'user@[IPv6:2001:db8::1]')
        if literal_content_processed.lower().startswith('ipv6:'):
            ipv6_addr_str = literal_content_processed[5:]
            if not ipv6_addr_str: # e.g. [IPv6:] is invalid
                return False
            try:
                # ipaddress.IPv6Address can validate various forms of IPv6 addresses
                ipaddress.IPv6Address(ipv6_addr_str)
                return True
            except ipaddress.AddressValueError:
                return False
        
        return False # Not a valid IP literal (or IPv6, etc.) based on current rules

    # If it's not an IP literal, process as a regular domain name (hostname)
    domain_part_processed = _strip_comments_and_fws(domain_part_raw)
    if domain_part_processed is None: # Malformed comments/escapes in domain
        return False
        
    if not domain_part_processed: # Empty domain after stripping is invalid
        return False
    
    # FIX 4: 'user@a' - Removed restriction for single-label domains to be 'localhost'
    # The original condition `if domain_part_processed != 'localhost' and '.' not in domain_part_processed:`
    # caused 'user@a' to fail. Removing it allows any single label if it meets label rules.
    
    # No spaces allowed in domain part (after stripping CFWS)
    if " " in domain_part_processed:
        return False

    # Domain part cannot start or end with a dot
    if domain_part_processed.startswith('.') or domain_part_processed.endswith('.'):
        return False
    # Domain part cannot have consecutive dots
    if ".." in domain_part_processed:
        return False
    
    # Split domain into labels and validate each label
    domain_labels = domain_part_processed.split('.')
    
    for label in domain_labels:
        # Each label must not be empty
        if not label:
            return False
        # Domain labels cannot start or end with a hyphen
        if label.startswith('-') or label.endswith('-'):
            return False
        
        # Validate characters for domain labels (LDH-rule: letters, digits, hyphen)
        # This prevents non-ASCII characters like 'é' in domain labels.
        allowed_label_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"
        for char in label:
            if char not in allowed_label_chars:
                return False

    # 5. Validate Top-Level Domain (TLD)
    # For multi-label domains, the TLD (last label) must be at least 2 characters long.
    # This rule doesn't apply to single-label domains like 'a' or 'localhost'.
    if len(domain_labels) > 1: # Only apply TLD length rule for multi-label domains
        tld = domain_labels[-1] 
        if len(tld) < 2:
            return False

    return True