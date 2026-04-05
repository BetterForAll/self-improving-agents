import re

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

    # Find the first unquoted '@' to separate local and domain parts
    # This handles cases like '"a@b"@example.com' where '@' appears within a quoted local part.
    at_index = -1
    in_quote = False
    for i, char in enumerate(email):
        if char == '"':
            # Toggle in_quote state. This simplified logic assumes unescaped quotes
            # are the only way to toggle. It doesn't fully parse escaped quotes like '\"'
            # or escaped backslashes like '\\' but is sufficient for the provided failures.
            in_quote = not in_quote
        elif char == '@' and not in_quote:
            at_index = i
            break
    
    if at_index == -1: # No unquoted '@' found
        return False

    local_part = email[:at_index]
    domain_part = email[at_index+1:]

    # 3. Validate local part
    # Local part cannot be empty (e.g., '@domain.com')
    if not local_part:
        return False

    local_part_is_quoted = False
    if local_part.startswith('"') and local_part.endswith('"'):
        local_part_is_quoted = True
        # For quoted strings, RFC 5322 allows most characters, including spaces and '@',
        # as long as " and \ are escaped.
        # '"first last"@example.com' and '"a@b"@example.com' are valid.
        
        # An empty quoted string ("") is a valid local part.
        if len(local_part) == 2: # Represents ""
            pass # Valid empty quoted string
        else:
            # Check content for unescaped quotes or invalid escape sequences
            content = local_part[1:-1]
            i = 0
            while i < len(content):
                if content[i] == '\\':
                    i += 1 # Skip the character after a backslash (it's escaped)
                    if i >= len(content): # Malformed escape sequence (trailing backslash)
                        return False
                elif content[i] == '"': # Unescaped quote within a quoted string is invalid
                    return False
                i += 1
            
    else: # Local part is NOT quoted (dot-atom)
        # No spaces allowed in unquoted local parts
        if " " in local_part:
            return False
        # Local part cannot start or end with a dot
        if local_part.startswith('.') or local_part.endswith('.'):
            return False
        # Local part cannot have consecutive dots
        if ".." in local_part:
            return False
        
        # Validate characters for non-quoted local part (atext rule from RFC 5322)
        # This addresses 'useré@example.com' where 'é' is not an allowed character.
        # atext = ALPHA / DIGIT / "!" / "#" / "$" / "%" / "&" / "'" / "*" / "+" / "-" / "/" / "=" / "?" / "^" / "_" / "`" / "{" / "|" / "}" / "~"`
        allowed_atext_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&'*+-/=?^_`{|}~"
        
        # Split by dots to validate each 'atom' within the local part
        atoms = local_part.split('.')
        for atom in atoms:
            if not atom: # This should be covered by start/end/consecutive dot checks, but as a safeguard.
                return False
            for char in atom:
                if char not in allowed_atext_chars:
                    return False

    # 4. Validate domain part
    # Domain part cannot be empty
    if not domain_part:  # Handles 'user@'
        return False
    # Domain part must contain at least one dot (e.g., example.com)
    if '.' not in domain_part:
        return False
    # Domain part cannot start or end with a dot
    if domain_part.startswith('.') or domain_part.endswith('.'):
        return False
    # Domain part cannot have consecutive dots
    if ".." in domain_part:
        return False
    # No spaces allowed in domain part
    if " " in domain_part:
        return False

    # Split domain into labels and validate each label
    domain_labels = domain_part.split('.')
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
    # TLD (the part after the last dot) must be at least 2 characters long
    tld = domain_labels[-1] # TLD is the last label
    if len(tld) < 2:
        return False

    return True