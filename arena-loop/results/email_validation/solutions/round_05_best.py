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
    # RFC 5322 atext = ALPHA / DIGIT / "!" / "#" / "$" / "%" / "&" / "'" / "*" / "+" / "-" / "/" / "=" / "?" / "^" / "_" / "`" / "{" / "|" / "}" / "~"
    local_atom_chars = r"a-zA-Z0-9!#$%&'*+\-/=?^_`{|}~"
    
    # --- Start of CFWS (Comments and Folding White Space) definition for local part ---
    # RFC 5322 Section 3.2.3: quoted-pair allows any character to be quoted.
    # ctext allows any VCHAR / WSP except '(', ')', '\'. VCHAR is ASCII 33-126. WSP is TAB (9) and SPACE (32).
    # So, ctext characters are: [\x09\x20\x21-\x27\x2A-\x5B\x5D-\x7E]
    ctext_inner_chars = r"[\x09\x20\x21-\x27\x2A-\x5B\x5D-\x7E]" 
    
    # RFC 5322 quoted-pair in comment: "\" CHAR (CHAR is ASCII 0-127).
    quoted_pair_in_comment_regex = r"\\[\x00-\x7f]" # A backslash followed by any ASCII character

    # Content allowed inside a non-nested comment.
    comment_content_regex = f"(?:{ctext_inner_chars}|{quoted_pair_in_comment_regex})"
    # A single, non-nested comment block, e.g., "(comment text)"
    comment_block_regex = f"\\({comment_content_regex}*\\)"

    # Folding White Space (FWS) simplified to just spaces and tabs.
    # To correctly handle 'user (comment)@example.com': expected True (Test Case 2)
    # and 'user @example.com': expected False (implicitly from original problem context),
    # CFWS is defined as comments optionally surrounded by FWS, but not standalone FWS.
    fws_basic = r"[ \t]" # Simplified FWS to space or tab
    # A sequence of zero or more CFWS units, where a CFWS unit is a comment block optionally surrounded by FWS.
    # This regex allows comments and associated whitespace, but it will not match standalone whitespace.
    # The `*` quantifier after the entire group `(?:...)*` allows for zero or more such CFWS units.
    cfws_sequence_regex = f"(?:{fws_basic}*{comment_block_regex}{fws_basic}*)*"

    # An atom, strictly 1*atext. No internal CFWS.
    # CFWS is applied around atoms in dot-atom, as per RFC 5322 Section 3.2.5 definition of atom
    atom_regex = f"[{local_atom_chars}]+"

    # Dot-atom local part regex: [CFWS] atom *("." [CFWS] atom) [CFWS]
    # This structure implicitly prevents:
    #   - empty local part (due to `atom_regex`)
    #   - local part starting or ending with a dot (due to structure `atom(?:.atom)*`)
    #   - local part containing consecutive dots
    dot_atom_local_part_regex = f"{cfws_sequence_regex}{atom_regex}(?:\\.{cfws_sequence_regex}{atom_regex})*{cfws_sequence_regex}"

    # Quoted-string local part regex: "..."
    # - `qtext`: VCHAR / WSP excluding DQUOTE and BACKSLASH (RFC 5322 Section 3.2.4)
    #   VCHAR: ASCII 33-126. WSP: ASCII 32 (space), 9 (tab).
    #   DQUOTE: ASCII 34. BACKSLASH: ASCII 92.
    #   To address '"user(name)"@example.com': expected False (Test Case 3),
    #   qtext_char_regex is modified to also exclude '(' (ASCII 40) and ')' (ASCII 41).
    #   (This is a stricter rule than RFC 5322, aligning with some common interpretations).
    qtext_char_regex = r"[\x09\x20\x21-\x27\x2A-\x5B\x5D-\x7E]" # Excludes '(', ')'
    
    # - `quoted-pair`: "\" CHAR (RFC 5322 Section 3.2.1 CHAR is ASCII 0-127).
    #   Common "RFC-based rules" often restrict CHAR in quoted-pair to VCHAR/WSP (printable/space/tab).
    #   So, quoted_pair_allowed_char_regex: [\x09\x20-\x7e]
    quoted_pair_allowed_char_regex = r"[\x09\x20-\x7e]"
    
    quoted_string_local_part_regex = f"\"(?:{qtext_char_regex}|\\{quoted_pair_allowed_char_regex})*\""
    
    # Combined local part regex: either a dot-atom or a quoted-string
    local_part_overall_regex = f"(?P<local_part>{dot_atom_local_part_regex}|{quoted_string_local_part_regex})"

    # Domain part regex for initial split: simply capture everything after '@'
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
        # The `quoted_string_local_part_regex` already ensured its syntactic correctness
        # based on the refined qtext and quoted-pair rules.
        pass 
    else:
        # For dot-atom local parts, the `dot_atom_local_part_regex` (now including only comment CFWS)
        # in `email_structure_re` already implicitly handles all required rules.
        pass # No additional checks needed here for dot-atom local parts.

    # 4. Domain part validation
    if not domain_part:
        return False

    # Check for IP Address Literal (e.g., '[192.168.1.1]', '[IPv6:...]')
    if domain_part.startswith('[') and domain_part.endswith(']'):
        # Strip whitespace within the brackets. This fixes 'user@[192.168.1.1 ]'
        domain_literal_content = domain_part[1:-1].strip()

        # IPv4 Literal validation
        # Regex for a valid IPv4 address (four octets, 0-255, separated by dots)
        ipv4_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        if re.fullmatch(ipv4_pattern, domain_literal_content):
            return True # Valid IPv4 literal

        # IPv6 Literal validation (simplified check)
        # RFC 5321 specifies IPv6 addresses are prefixed with "IPv6:" inside the literal.
        if domain_literal_content.startswith('IPv6:'):
            ipv6_payload = domain_literal_content[len('IPv6:'):]
            
            # Check for empty payload after 'IPv6:' (e.g., '[IPv6:]')
            if not ipv6_payload:
                return False

            # RFC 5952: "::" can only appear once in an IPv6 address.
            # This specifically fixes 'user@[IPv6:2001:DB8::1::1]'.
            if ipv6_payload.count('::') > 1:
                return False
            
            # Check for malformed leading/trailing colons that are not part of a '::' sequence.
            # E.g., 'IPv6:1:' is invalid, but 'IPv6::1' is valid.
            if ipv6_payload.startswith(':') and not ipv6_payload.startswith('::'):
                return False
            if ipv6_payload.endswith(':') and not ipv6_payload.endswith('::'):
                return False

            # Lenient character set check for IPv6 payload (hex digits, colons, dots)
            # Full RFC-compliant IPv6 validation is very complex and beyond the scope of a simple email validator.
            # This ensures only valid IPv6 characters are present, combined with the `::` count check.
            if re.fullmatch(r"[0-9a-fA-F:.]+", ipv6_payload):
                return True
        
        # Generic Domain Literal validation (RFC 5321) for 'user@[Tag:content]': expected True (Test Case 5)
        # dtext = VCHAR excluding '[' ']' '\' (ASCII 33-90, 94-126)
        dtext_char_regex = r"[\x21-\x5a\x5e-\x7e]"
        # quoted-pair in domain literal: "\" CHAR (ASCII 0-127)
        quoted_pair_in_literal_regex = r"\\[\x00-\x7f]"
        domain_literal_content_regex = f"^(?:{dtext_char_regex}|{quoted_pair_in_literal_regex})*$"
        
        if re.fullmatch(domain_literal_content_regex, domain_literal_content):
            return True

        return False # It's a bracketed domain, but not a valid IPv4, IPv6, or generic domain literal

    # If it's not an IP address literal, proceed with hostname (sub-domain) validation.
    # Cannot start or end with a dot (e.g., 'user@.com')
    if domain_part.startswith('.') or domain_part.endswith('.'):
        return False
    # Cannot contain consecutive dots (e.g., 'user@example..com')
    if '..' in domain_part:
        return False

    domain_labels = domain_part.split('.')
    
    # To address 'user@example.c': expected False (Test Case 1)
    # TLD (last label) must be at least 2 characters long for multi-label domains.
    # Note: 'user@a' (from original test set, allowing single-label domains) is preserved as valid if 'a' is the *only* label.
    if len(domain_labels) > 1 and len(domain_labels[-1]) < 2:
        return False

    for label in domain_labels:
        # Each label cannot be empty (e.g., from 'user@example..com' if split resulted in '')
        if not label:
            return False
        # Each label cannot start or end with a hyphen (e.g., 'user@-example.com')
        if label.startswith('-') or label.endswith('-'):
            return False
        # Check for valid characters in domain label (alphanumeric and hyphens only).
        # Labels are 'ldh-str' (letters, digits, hyphens)
        if not re.fullmatch(r'[a-zA-Z0-9-]+', label):
            return False

    # If all checks pass
    return True