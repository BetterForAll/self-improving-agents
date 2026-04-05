import re

def validate_email(email):
    """Check if an email address is valid.

    Args:
        email: str, the email address to validate

    Returns: True if valid, False if invalid
    """
    # 1. Overall length check (RFC 5321 specifies 254 characters max)
    if len(email) > 254:
        return False

    # 2. Must contain exactly one '@' symbol
    if email.count('@') != 1:
        return False

    local_part, domain_part = email.split('@')

    # 3. Local and domain parts must not be empty
    if not local_part or not domain_part:
        return False

    # 4. Local part length check (RFC 5321 specifies max 64 characters)
    if len(local_part) > 64:
        return False

    # 5. Domain part length check (RFC 5321 specifies max 255 characters, including dots)
    # This refers to the domain string itself, not including the local part or '@'.
    # The overall email length is checked separately.
    if len(domain_part) > 255:
        return False

    # --- Local Part Validation ---
    # Allowed characters for dot-atom: alphanumeric, and !#$%&'*+-/=?^_`{|}~
    # This regex ensures:
    # - Starts with one or more valid local characters (non-dot).
    # - Optionally followed by a sequence of a dot and one or more valid local characters (non-dot).
    # This implicitly disallows leading/trailing dots and consecutive dots.
    # This implementation focuses on the common "dot-atom" local part and does not
    # support "quoted-string" local parts (e.g., "John Doe"@example.com) for practical reasons,
    # as they are rare and complex to validate with regex alone.
    local_part_pattern = r"^[a-zA-Z0-9!#$%&'*+-/=?^_`{|}~]+(?:\.[a-zA-Z0-9!#$%&'*+-/=?^_`{|}~]+)*$"
    if not re.fullmatch(local_part_pattern, local_part):
        return False

    # --- Domain Part Validation ---
    # Check for IP address literal domain [IPv4] or [IPv6:...] (RFC 5321, 4.1.3)
    if domain_part.startswith('[') and domain_part.endswith(']'):
        ip_literal = domain_part[1:-1] # Remove brackets

        # Attempt to validate as IPv4 address literal (e.g., [192.168.1.1])
        # Regex for an octet (0-255)
        octet = r"(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])"
        ipv4_pattern = rf"^{octet}\.{octet}\.{octet}\.{octet}$"
        if re.fullmatch(ipv4_pattern, ip_literal):
            return True

        # Attempt to validate as IPv6 address literal (e.g., [IPv6:2001:db8::1])
        # The literal must explicitly start with "IPv6:" as per RFC 5321.
        if ip_literal.lower().startswith('ipv6:'):
            ipv6_address_part = ip_literal[5:] # Remove "IPv6:" prefix

            # A comprehensive IPv6 regex is very complex and can be excessively long.
            # This pattern is derived from commonly used regex for IPv6 validation
            # (e.g., from Django's validator), adapted for clarity and Python's re.
            # It covers full, compressed (::), and embedded IPv4 forms.
            # Note: This is for the address *after* "IPv6:".
            ipv6_pattern = (
                r'^('
                r'([0-9a-fA-F]{1,4}:){7}([0-9a-fA-F]{1,4}|:)|'  # Full form: xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx OR xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:
                r'([0-9a-fA-F]{1,4}:){6}(:[0-9a-fA-F]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:)|' # 6 groups + TLD or IPv4 or nothing
                r'([0-9a-fA-F]{1,4}:){5}(((:[0-9a-fA-F]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:)|' # 5 groups + TLD(s) or IPv4 or nothing
                r'([0-9a-fA-F]{1,4}:){4}(((:[0-9a-fA-F]{1,4}){1,3})|((:[0-9a-fA-F]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)|' # 4 groups + TLD(s) or IPv4 or nothing
                r'([0-9a-fA-F]{1,4}:){3}(((:[0-9a-fA-F]{1,4}){1,4})|((:[0-9a-fA-F]{1,4}){1,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)|' # 3 groups + TLD(s) or IPv4 or nothing
                r'([0-9a-fA-F]{1,4}:){2}(((:[0-9a-fA-F]{1,4}){1,5})|((:[0-9a-fA-F]{1,4}){1,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)|' # 2 groups + TLD(s) or IPv4 or nothing
                r'([0-9a-fA-F]{1,4}:){1}(((:[0-9a-fA-F]{1,4}){1,6})|((:[0-9a-fA-F]{1,4}){1,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)|' # 1 group + TLD(s) or IPv4 or nothing
                r':(((:[0-9a-fA-F]{1,4}){1,7})|((:[0-9a-fA-F]{1,4}){1,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)' # Start with '::' and various options
                r')$'
            )
            if re.fullmatch(ipv6_pattern, ipv6_address_part):
                return True
        # If it's an IP literal (starts with '[' ends with ']') but does not match
        # valid IPv4 or IPv6 (with "IPv6:" prefix), then it's an invalid format.
        return False
    # End of IP address literal check.

    # If not an IP literal, continue with standard hostname validation.
    # 1. No leading/trailing dots, no consecutive dots in the domain part.
    # This prevents 'example..com', '.example.com', 'example.com.'
    if domain_part.startswith('.') or domain_part.endswith('.') or '..' in domain_part:
        return False

    # Split domain into labels (e.g., "example.com" -> ["example", "com"])
    domain_labels = domain_part.split('.')

    # 2. Domain must have at least two labels (e.g., "example.com" is valid, "example" is not for public email)
    # This is a common practical rule for public email addresses, though RFCs technically allow
    # single-label domains (e.g., "localhost") in certain contexts. For a general validator, this is sensible.
    if len(domain_labels) < 2:
        return False

    # 3. Validate each label in the domain part
    for label in domain_labels:
        if not label: # An empty label indicates consecutive dots or leading/trailing dots (already checked, but good redundancy)
            return False
        if len(label) > 63: # Each label max 63 characters (RFC 1035)
            return False
        # Each label must start and end with an alphanumeric character.
        # It can contain alphanumeric characters or hyphens in between.
        # Examples: "example", "sub-domain", "test123" are valid labels.
        # "-example", "example-" or "example.-com" are invalid.
        # This regex strictly follows RFC 1035 for hostname labels.
        label_pattern = r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$"
        if not re.fullmatch(label_pattern, label):
            return False

    # 4. TLD (Top-Level Domain) validation
    # TLD is the last label. Must be at least 2 characters long.
    # It has already been validated against `label_pattern` in the loop above to ensure
    # it contains valid characters (alphanumeric and hyphens, not starting/ending with hyphen).
    tld = domain_labels[-1]
    if len(tld) < 2: # e.g., 'c' in 'example.c'
        return False

    return True