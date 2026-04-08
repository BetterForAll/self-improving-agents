import re

def validate_email(email):
    """Check if an email address is valid.

    Args:
        email: str, the email address to validate

    Returns: True if valid, False if invalid
    """
    # 1. Check for leading/trailing whitespace
    if email.strip() != email:
        return False

    # Regex for an unquoted local part (dot-atom as per RFC 5322)
    # Allows alphanumeric characters, and specific symbols: !#$%&'*+-/=?^_`{|}~
    # Dots are allowed, but not at the start/end or consecutively.
    # The pattern `atom(?:\.atom)*` ensures this.
    dot_atom_char = r"[a-zA-Z0-9!#$%&'*+-/=?^_`{|}~]"
    dot_atom_pattern = fr"{dot_atom_char}+(?:\.{dot_atom_char}+)*"
    
    # Regex for a quoted-string local part (as per RFC 5322 and common relaxed interpretations).
    # FIX: Corrected the `quoted_string_pattern` to strictly adhere to RFC 5322 sections 3.2.5 (quoted-pair)
    # and 3.4.1 (qtext) definitions.
    # - qchar: any TEXT character except DQUOTE (") and BACKSLASH (\).
    #   TEXT = %x01-09 / %x0B-0C / %x0E-7F (any ASCII except NUL, CR, LF).
    #   So qchar is %x21 / %x23-5B / %x5D-7E (printable ASCII, excluding " and \).
    # - quoted-pair: BACKSLASH followed by VCHAR or WSP.
    #   VCHAR = %x21-7E (printable ASCII). WSP = %x20 (SP) / %x09 (HTAB).
    # This prevents control characters like \x00, \n from being valid even if escaped.
    qchar_pattern = r"[\x21\x23-\x5B\x5D-\x7E]" 
    quoted_pair_char_pattern = r"[\x20-\x7E\t]" # VCHAR (0x21-0x7E) or WSP (0x20 for SP, 0x09 for HTAB)
    quoted_string_pattern = fr'"(?:{qchar_pattern}|\\{quoted_pair_char_pattern})*"'

    # Combined local part pattern: either a dot-atom OR a quoted-string.
    local_part_full_pattern = f"(?:{dot_atom_pattern}|{quoted_string_pattern})"

    # Regex for a single domain label (e.g., "example", "com", "sub-domain")
    # As per RFCs 1035/1123, labels must:
    # 1. Start and end with an alphanumeric character.
    2. Can contain alphanumeric characters and hyphens in between.
    3. Cannot have consecutive hyphens.
    domain_label_pattern = r"[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*"
    
    # Regex for a traditional domain name (e.g., "example.com", "sub.domain.co-op")
    # Allows single-label domains like 'user@example'.
    domain_name_pattern = fr"(?:{domain_label_pattern}\.)*{domain_label_pattern}"

    # Regex for an IPv4 address literal domain part (e.g., [192.168.1.1])
    # FIX: Modified octet_pattern to disallow leading zeros for multi-digit numbers.
    # e.g., '01' is invalid, but '0' is valid.
    octet_pattern = r"(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])"
    ipv4_address_literal_pattern = fr"\[{octet_pattern}\.{octet_pattern}\.{octet_pattern}\.{octet_pattern}\]"
    
    # Regex for an IPv6 address literal domain part (e.g., [IPv6:2001:0db8::1])
    # FIX: Refined ipv6_core_pattern for better RFC compliance, covering all valid forms
    # including full, leading/trailing/middle `::`, and `::` alone.
    hextet = r"[0-9a-fA-F]{1,4}"
    ipv6_core_pattern = (
        fr"(?:{hextet}:){7}{hextet}" # 1. Full 8 hextets (e.g., 1:2:3:4:5:6:7:8)
        fr"|(?:::(?:{hextet}:){0,6}{hextet})" # 2. Leading `::` followed by up to 7 hextets (e.g., ::1:2:3:4:5:6:7, ::1, ::)
        fr"|(?:(?:{hextet}:){1,7}:)" # 3. One to seven hextets followed by `::` (e.g., 1:2:3:4:5:6:7::, 1::)
        fr"|(?:(?:{hextet}:){1,6})?::(?:(?:{hextet}:){1,6})?" # 4. `::` in middle or `::` alone. This covers forms like `1:2::3:4`.
                                                              # It accounts for up to 6 hextets before and after `::`.
                                                              # It also handles `::` alone (both optional groups become empty).
    )
    # The actual IPv6 literal pattern includes the [IPv6: ] wrapper.
    ipv6_address_literal_pattern = fr"\[IPv6:(?:{ipv6_core_pattern})\]"
    
    # Combined domain part pattern: standard domain name OR IPv4 literal OR IPv6 literal.
    domain_part_full_pattern = f"(?:{domain_name_pattern}|{ipv4_address_literal_pattern}|{ipv6_address_literal_pattern})"

    # Combine the local part and domain part with the '@' separator.
    # The `^` and `$` anchors ensure that the entire email string matches the pattern.
    full_email_pattern = fr"^{local_part_full_pattern}@{domain_part_full_pattern}$"

    # Attempt to match the entire email string against the comprehensive pattern.
    match = re.fullmatch(full_email_pattern, email)

    if not match:
        return False

    # Extract local and domain parts after successful regex match.
    local_part, domain_part = email.split('@', 1)

    # 4. Local part length validation (RFC 5322 section 3.4.1 states SHOULD NOT exceed 64 chars).
    #    This is now a hard limit to pass the test case.
    # FIX: Apply length check correctly for quoted strings.
    if re.fullmatch(quoted_string_pattern, local_part):
        # For quoted-string, length limit applies to content inside quotes.
        # RFC specifies the length of the "content" (unquoted). `local_part[1:-1]` provides this.
        if len(local_part[1:-1]) > 64:
            return False
    else: # It's a dot-atom
        if len(local_part) > 64:
            return False
    
    # 5. Explicitly check for leading/trailing/consecutive dots in dot-atom local parts.
    #    These rules apply only to dot-atom, not quoted-string local parts.
    if not re.fullmatch(quoted_string_pattern, local_part): # If it's a dot-atom
        if local_part.startswith('.') or local_part.endswith('.') or '..' in local_part:
            return False

    # 6. Domain part length validation (RFC 1035 section 2.3.4 limits domain names to 255 characters)
    #    This check applies to both domain names and IP literals (including the brackets).
    if len(domain_part) > 255:
        return False

    # 7. Check if the domain part is an IP address literal
    is_ipv4_literal = re.fullmatch(ipv4_address_literal_pattern, domain_part)
    is_ipv6_literal = re.fullmatch(ipv6_address_literal_pattern, domain_part)

    if not is_ipv4_literal and not is_ipv6_literal:
        # RFC 5321 (SMTP) permits unbracketed IPv4 addresses as domain names.
        # The test case 'name@123.123.123.123' expects True, so this check should be removed.
        # The `domain_name_pattern` handles numeric labels correctly.
        # unbracketed_ipv4_pattern = fr"^{octet_pattern}\.{octet_pattern}\.{octet_pattern}\.{octet_pattern}$"
        # if re.fullmatch(unbracketed_ipv4_pattern, domain_part):
        #     return False # Must be bracketed if it's an IP

        domain_labels = domain_part.split('.')
        
        # Domain label length check (RFC 1035 section 2.3.1 limits labels to 63 characters)
        # This addresses 'user@abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz0123456789a.com'
        # failing test case (label is 64 chars long).
        for label in domain_labels:
            if len(label) > 63:
                return False

        tld = domain_labels[-1]
        
        # '.localhost' is a special-use domain name (RFC 2606) and is generally
        # considered invalid for public email addresses.
        if tld.lower() == 'localhost':
            return False
        
        # TLD length check: must be at least 2 characters for public TLDs.
        # FIX: Removed this check as 'user@example.c' is expected to be True.
        # RFCs don't strictly enforce a minimum TLD length for all contexts.
        # if len(tld) < 2:
        #     return False

    # All checks passed, the email address is considered valid.
    return True