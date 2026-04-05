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
    # The RFC mentions 255 for the FQDN, which is essentially the domain_part.
    if len(domain_part) > 255:
        return False

    # --- Local Part Validation ---
    # Allowed characters for dot-atom: alphanumeric, and !#$%&'*+-/=?^_`{|}~
    # Dots are allowed, but not at start/end, and not consecutive.
    # This regex ensures:
    # - Starts with one or more valid local characters (non-dot).
    # - Optionally followed by a sequence of a dot and one or more valid local characters (non-dot).
    # This implicitly disallows leading/trailing dots and consecutive dots.
    # This implementation focuses on the common "dot-atom" local part and does not
    # support "quoted-string" local parts (e.g., "John Doe"@example.com) for practical reasons,
    # as they are rare and complex to validate.
    local_part_pattern = r"^[a-zA-Z0-9!#$%&'*+-/=?^_`{|}~]+(?:\.[a-zA-Z0-9!#$%&'*+-/=?^_`{|}~]+)*$"
    if not re.fullmatch(local_part_pattern, local_part):
        return False

    # --- Domain Part Validation ---

    # Check for Address Literal (e.g., [192.168.1.1] or [IPv6:...]) as per RFC 5321, Section 4.1.3
    if domain_part.startswith('[') and domain_part.endswith(']'):
        address_literal_content = domain_part[1:-1]

        # IPv4 Literal Validation (e.g., [192.168.1.1])
        # Regex for a valid IPv4 address
        ipv4_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        if re.fullmatch(ipv4_pattern, address_literal_content):
            return True

        # IPv6 Literal Validation (e.g., [IPv6:2001:db8::1])
        elif address_literal_content.lower().startswith('ipv6:'):
            ipv6_addr = address_literal_content[5:]
            # A robust regex for IPv6 address (excluding the "IPv6:" prefix and outer brackets).
            # This regex covers full, compressed, and IPv4-mapped IPv6 formats as permitted in email.
            # Derived from common RFC-compliant IPv6 validation patterns.
            ipv6_addr_re = (
                r"^((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|"  # Full address or ending with ::
                r"(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1?\d?\d)(\.(25[0-5]|2[0-4]\d|1?\d?\d)){3})|:))|"  # 6 groups and an IPv4 or ::
                r"(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1?\d?\d)(\.(25[0-5]|2[0-4]\d|1?\d?\d)){3})|:))|"  # 5 groups and 1-2 more or IPv4 or ::
                r"(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1?\d?\d)(\.(25[0-5]|2[0-4]\d|1?\d?\d)){3}))|:))|"  # 4 groups...
                r"(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1?\d?\d)(\.(25[0-5]|2[0-4]\d|1?\d?\d)){3}))|:))|"  # 3 groups...
                r"(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1?\d?\d)(\.(25[0-5]|2[0-4]\d|1?\d?\d)){3}))|:))|"  # 2 groups...
                r"(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1?\d?\d)(\.(25[0-5]|2[0-4]\d|1?\d?\d)){3}))|:))|"  # 1 group...
                r"(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1?\d?\d)(\.(25[0-5]|2[0-4]\d|1?\d?\d)){3}))|:)))$" # Leading or all ::
            )
            if re.fullmatch(ipv6_addr_re, ipv6_addr):
                return True
            else:
                return False
        else:
            # It's an address literal but not a recognized type (IPv4 or IPv6)
            return False
    
    # If not an address literal, proceed with domain name validation
    # 1. No leading/trailing dots, no consecutive dots in the domain part.
    if domain_part.startswith('.') or domain_part.endswith('.') or '..' in domain_part:
        return False

    # Split domain into labels (e.g., "example.com" -> ["example", "com"])
    domain_labels = domain_part.split('.')

    # 2. Domain must have at least two labels for common public email addresses
    # (e.g., "example.com" is valid, "example" is not for public email).
    # RFC 5321 does allow single-label domains like "localhost", but this function
    # targets typical internet email addresses which usually have a TLD.
    if len(domain_labels) < 2:
        return False

    # 3. Validate each label in the domain part
    for label in domain_labels:
        if not label: # Empty label (e.g., "example..com" would result in an empty string in labels)
            return False
        if len(label) > 63: # Each label max 63 characters (RFC 1035)
            return False
        # Each label must start and end with an alphanumeric character.
        # Can contain alphanumeric characters or hyphens in between.
        # Examples: "example", "sub-domain", "test123" are valid labels.
        # "-example", "example-" are invalid.
        # This regex strictly follows RFC 1035 for hostname labels.
        # This also correctly handles Punycode labels (e.g., xn--...)
        label_pattern = r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$"
        if not re.fullmatch(label_pattern, label):
            return False

    # 4. TLD (Top-Level Domain) validation
    # TLD is the last label. Must be at least 2 characters long.
    # It has already been validated against `label_pattern` in the loop above to ensure
    # it contains valid characters (alphanumeric and hyphens, not starting/ending with hyphen).
    tld = domain_labels[-1]
    if len(tld) < 2:
        return False

    return True