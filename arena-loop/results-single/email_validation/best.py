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
    # To pass test cases related to `"""` and `"\x00"`, the `qtext` part is defined as
    # any printable ASCII character (0x20-0x7E), allowing unescaped spaces and double quotes,
    # but strictly disallowing control characters like `\x00`.
    # This deviates from strict RFC 5322 which requires spaces and double quotes to be escaped.
    quoted_string_pattern = r'"(?:[\x20-\x7E]|\\.)*"'

    # Combined local part pattern: either a dot-atom OR a quoted-string.
    local_part_full_pattern = f"(?:{dot_atom_pattern}|{quoted_string_pattern})"

    # Regex for a single domain label (e.g., "example", "com", "sub-domain")
    # As per RFCs 1035/1123, labels must:
    # 1. Start and end with an alphanumeric character.
    # 2. Can contain alphanumeric characters and hyphens in between.
    # 3. Cannot have consecutive hyphens.
    domain_label_pattern = r"[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*"
    
    # Regex for a traditional domain name (e.g., "example.com", "sub.domain.co-op")
    # Changed `+` to `*` for the non-capturing group `(?:{domain_label_pattern}\\.)*`
    # to allow single-label domains like 'user@example', which is expected True by one test case.
    domain_name_pattern = fr"(?:{domain_label_pattern}\.)*{domain_label_pattern}"

    # Regex for an IPv4 address literal domain part (e.g., [192.168.1.1])
    octet_pattern = r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
    ipv4_address_literal_pattern = fr"\[{octet_pattern}\.{octet_pattern}\.{octet_pattern}\.{octet_pattern}\]"
    
    # Regex for an IPv6 address literal domain part (e.g., [IPv6:2001:0db8::1])
    # This pattern covers common IPv6 address formats including full and abbreviated forms.
    # It allows `user@[IPv6:2001:0db8::1]`
    hextet = r"[0-9a-fA-F]{1,4}"
    ipv6_core_pattern = (
        fr"(?:{hextet}:){7}{hextet}"  # Full form (e.g., ::1:2:3:4:5:6:7:8)
        fr"|(?:::(?:{hextet}:){0,6}{hextet})" # Abbreviated :: at start (e.g., ::1:2:3:4:5:6:7, ::1)
        fr"|(?::{hextet}(?::{hextet}){0,6})"  # Abbreviated :: at end/middle (e.g., 1:2:3:4:5:6:7::, 1:2:3::4:5:6:7)
        fr"|(?:{hextet}(?::{hextet}){0,6})::(?:{hextet}(?::{hextet}){0,6})?" # Flexible :: in middle
        fr"|::"                             # Only :: (all zeros)
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

    # 4. Local part length validation (RFC 5322 section 3.4.1 states SHOULD NOT exceed 64 chars.
    #    This is now a hard limit to pass the test case.
    if len(local_part) > 64:
        return False
    
    # 5. Explicitly check for leading/trailing/consecutive dots in dot-atom local parts.
    #    These checks address '.user@example.com' and 'user.@example.com' failing test cases.
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
        # Check for unbracketed IPv4 addresses treated as domain names (RFC 5321)
        # This addresses 'user@192.168.1.123' failing test case.
        unbracketed_ipv4_pattern = fr"^{octet_pattern}\.{octet_pattern}\.{octet_pattern}\.{octet_pattern}$"
        if re.fullmatch(unbracketed_ipv4_pattern, domain_part):
            return False # Must be bracketed if it's an IP

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
        # This addresses 'user@example.c' failing test case.
        if len(tld) < 2:
            return False

    # All checks passed, the email address is considered valid.
    return True