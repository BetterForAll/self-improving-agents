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
    # This pattern: atom ( . atom )* ensures this.
    dot_atom_pattern = r"[a-zA-Z0-9!#$%&'*+-/=?^_`{|}~]+(?:\.[a-zA-Z0-9!#$%&'*+-/=?^_`{|}~]+)*"
    
    # Regex for a quoted-string local part (as per RFC 5322)
    # Allows almost any character inside quotes, except an unescaped double quote (") or backslash (\).
    quoted_string_pattern = r'"(?:[^"\\]|\\.)*"'

    # Combined local part pattern: either a dot-atom OR a quoted-string.
    local_part_full_pattern = f"(?:{dot_atom_pattern}|{quoted_string_pattern})"

    # Regex for a single domain label (e.g., "example", "com", "sub-domain")
    # As per RFCs 1035/1123, labels must:
    # 1. Start and end with an alphanumeric character.
    # 2. Can contain alphanumeric characters and hyphens in between.
    # 3. Cannot have consecutive hyphens.
    # 4. Cannot be all-numeric (RFC 1123, for hostnames to distinguish from IP addresses).
    # The pattern `(?![0-9]+$)[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*` satisfies these.
    domain_label_pattern = r"(?![0-9]+$)[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*"
    
    # Regex for a traditional domain name (e.g., "example.com", "sub.domain.co-op")
    # This pattern enforces one or more labels separated by dots, where each label
    # adheres to `domain_label_pattern`.
    domain_name_pattern = f"(?:{domain_label_pattern}\\.)+{domain_label_pattern}"

    # Regex for an IPv4 address literal domain part (e.g., [192.168.1.1])
    octet_pattern = r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
    ipv4_address_literal_pattern = fr"\[{octet_pattern}\.{octet_pattern}\.{octet_pattern}\.{octet_pattern}\]"
    
    # Regex for an IPv6 address literal domain part (e.g., [IPv6:2001:0db8::1])
    # This pattern is a pragmatic simplification of the full IPv6 address specification
    # (RFC 4291) to cover common forms including full and compressed addresses,
    # without trying to validate every single obscure IPv6 variation (e.g., mixed IPv4-in-IPv6).
    hextet = r"[0-9a-fA-F]{1,4}"
    ipv6_addr_core_pattern = (
        fr"(?:{hextet}:){7}{hextet}" # Full IPv6 (8 hextets)
        r"|(?:::(?:[0-9a-fA-F]{1,4}:){0,5}[0-9a-fA-F]{1,4})" # Compressed leading `::` (up to 6 hextets after)
        r"|(?:[0-9a-fA-F]{1,4}::(?:[0-9a-fA-F]{1,4}:){0,4}[0-9a-fA-F]{1,4})" # Compressed middle `::` (1 to 6 hextets before, 1 to 5 after)
        r"|(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}::" # Compressed trailing `::` (up to 7 hextets before)
        r"|::" # Smallest IPv6 address (just `::`)
    )
    ipv6_address_literal_pattern = fr"\[IPv6:{ipv6_addr_core_pattern}\]"

    # Combined domain part pattern: standard domain name, IPv4 literal, OR IPv6 literal.
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

    # 4. Local part length validation (RFC 5322 section 3.4.1: SHOULD NOT exceed 64 chars.
    #    Treated as a hard error in many practical validators.)
    if len(local_part) > 64:
        return False

    # 5. Domain part length validation (RFC 1035 section 2.3.4 limits domain names to 255 characters)
    # This check applies to both domain names and IP literals (including the brackets).
    if len(domain_part) > 255:
        return False

    # 6. Top-Level Domain (TLD) and individual label specific checks
    is_ipv4_literal = re.fullmatch(ipv4_address_literal_pattern, domain_part)
    is_ipv6_literal = re.fullmatch(ipv6_address_literal_pattern, domain_part)

    if not is_ipv4_literal and not is_ipv6_literal:
        domain_labels = domain_part.split('.')
        tld = domain_labels[-1]
        
        # Check individual domain label length (RFC 1035 section 2.3.1: max 63 characters)
        for label in domain_labels:
            if len(label) > 63:
                return False

        # '.localhost' is a special-use domain name (RFC 2606) and is generally
        # considered invalid for public email addresses.
        if tld.lower() == 'localhost':
            return False
        
        # TLDs are generally expected to be at least 2 characters long for practical email validation.
        # This prevents single-character TLDs like '.c'
        if len(tld) < 2:
            return False

    # All checks passed, the email address is considered valid.
    return True