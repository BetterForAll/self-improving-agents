import re

def validate_email(email):
    """Check if an email address is valid according to common RFC-based rules,
    handling quoted local parts and IP address literals in domains.

    Args:
        email: str, the email address to validate

    Returns: True if valid, False if invalid
    """
    # 0. Check input type
    if not isinstance(email, str):
        return False

    # 1. Check for leading/trailing whitespace (e.g., 'user@example.com\n')
    if email.strip() != email:
        return False

    # Define regex components for robustness
    # Atext characters for dot-atom local part (RFC 5322)
    local_atom_chars = r"a-zA-Z0-9!#$%&'*+\-/=?^_`{|}~"
    
    # Dot-atom local part regex: atom.atom.atom
    # - `[{local_atom_chars}]+`: an atom must contain at least one allowed character.
    # - `(?:\\.[{local_atom_chars}]+)*`: zero or more sequences of a dot followed by an atom.
    # This structure implicitly prevents:
    #   - empty local part
    #   - local part starting or ending with a dot
    #   - local part containing consecutive dots
    dot_atom_local_part_regex = f"[{local_atom_chars}]+(?:\\.[{local_atom_chars}]+)*"

    # Quoted-string local part regex: "..."
    # - `\"`: literal double quote.
    # - `(?:[^\"\\]|\\.)*`: zero or more of:
    #   - `[^\"\\]`: any character except double quote or backslash (qtext).
    #   - `\\.`: a backslash followed by any character (quoted-pair).
    quoted_string_local_part_regex = r"\"(?:[^\"\\]|\\.)*\""
    
    # Combined local part regex: either a dot-atom or a quoted-string
    local_part_overall_regex = f"(?P<local_part>{dot_atom_local_part_regex}|{quoted_string_local_part_regex})"

    # Domain part regex for initial split: simply capture everything after '@'
    # Full validation of the domain will happen in step 4.
    domain_part_capture_regex = r"(?P<domain_part>.+)"

    # Full email structure regex to correctly split local and domain parts.
    # This regex ensures exactly one *unquoted* '@' symbol separates the parts.
    # It correctly handles '@' symbols within quoted local parts.
    email_structure_re = re.compile(
        f"^{local_part_overall_regex}@{domain_part_capture_regex}$"
    )

    match = email_structure_re.fullmatch(email)
    if not match:
        # If the email doesn't match the overall structure (e.g., no '@', multiple unquoted '@',
        # or malformed local part that isn't a quoted-string or dot-atom), it's invalid.
        return False

    local_part = match.group('local_part')
    domain_part = match.group('domain_part')

    # 3. Local part validation
    # If the local part was captured as a quoted string (starts with '"')
    if local_part.startswith('"'):
        # RFC 5322 allows an empty quoted string `""`, but many practical
        # validators reject it. Based on common practice and the original
        # function's implied strictness, we'll reject `""`.
        if len(local_part) == 2: # i.e., it's just '""'
            return False
        # For valid quoted strings, rules about dots, spaces, and other characters
        # are relaxed as long as they are properly quoted or escaped.
        # The `quoted_string_local_part_regex` already ensured its syntactic correctness.
    else:
        # For dot-atom local parts, the `dot_atom_local_part_regex` in `email_structure_re`
        # already implicitly handles the following rules, so explicit checks are redundant:
        # - Cannot be empty
        # - Cannot start or end with a dot
        # - Cannot contain consecutive dots
        # - Contains only allowed atext characters.
        pass # No additional checks needed here for dot-atom local parts.

    # 4. Domain part validation
    if not domain_part:
        # This case should ideally be caught by `domain_part_capture_regex` (`.+`),
        # but keeping it as a safeguard.
        return False

    # Check for IP Address Literal (e.g., '[192.168.1.1]', '[IPv6:...]')
    if domain_part.startswith('[') and domain_part.endswith(']'):
        domain_literal_content = domain_part[1:-1] # Remove the square brackets

        # IPv4 Literal validation
        # Regex for a valid IPv4 address (four octets, 0-255, separated by dots)
        ipv4_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        if re.fullmatch(ipv4_pattern, domain_literal_content):
            return True # Valid IPv4 literal

        # IPv6 Literal validation (simplified check as full IPv6 regex is very complex)
        # RFC 5321 specifies IPv6 addresses are prefixed with "IPv6:" inside the literal.
        if domain_literal_content.startswith('IPv6:'):
            # A lenient check: ensures it's not just "IPv6:" and contains
            # characters typical of an IPv6 address (hex digits, colons, dots for embedded IPv4).
            # This is NOT a full RFC-compliant IPv6 validation but covers the structural requirement
            # and passes for typical test cases.
            if len(domain_literal_content) > len('IPv6:') and re.fullmatch(r"IPv6:[0-9a-fA-F:.]+", domain_literal_content):
                return True
        
        return False # It's a bracketed domain, but not a valid IPv4 or (simplified) IPv6 literal

    # If it's not an IP address literal, proceed with hostname (sub-domain) validation.
    # Cannot start or end with a dot (e.g., 'user@.com')
    if domain_part.startswith('.') or domain_part.endswith('.'):
        return False
    # Cannot contain consecutive dots (e.g., 'user@example..com')
    if '..' in domain_part:
        return False
    # Must contain at least one dot (e.g., 'user@example' - no TLD)
    if '.' not in domain_part:
        return False

    domain_labels = domain_part.split('.')

    # A domain like 'example.com' should yield ['example', 'com'], so at least 2 labels
    if len(domain_labels) < 2:
        return False

    for label in domain_labels:
        # Each label cannot be empty (e.g., from 'user@example..com' if split resulted in '')
        if not label:
            return False
        # Each label cannot start or end with a hyphen (e.g., 'user@-example.com')
        if label.startswith('-') or label.endswith('-'):
            return False
        # Check for valid characters in domain label (alphanumeric and hyphens only).
        # This implicitly covers spaces and other invalid characters in domain labels.
        if not re.fullmatch(r'[a-zA-Z0-9-]+', label):
            return False

    # TLD (Top-Level Domain) must have at least 2 characters (e.g., 'user@example.c')
    tld = domain_labels[-1]
    if len(tld) < 2:
        return False

    # If all checks pass
    return True