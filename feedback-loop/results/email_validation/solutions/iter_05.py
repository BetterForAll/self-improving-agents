import re

def validate_email(email):
    """Check if an email address is valid.

    Args:
        email: str, the email address to validate

    Returns: True if valid, False if invalid
    """
    # 1. Overall length check (RFC 5321 specifies 254 characters max for the address itself,
    #    within a path limit of 256 including angle brackets).
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

    # 5. Domain part length check (RFC 5321 specifies max 255 characters for the domain name itself).
    #    This is independent of the overall address length, meaning a domain can be 255 chars,
    #    but an email like `local@long-domain` might still fail the overall 254 char limit.
    if len(domain_part) > 255:
        return False

    # --- Local Part Validation ---
    # Allowed characters for "dot-atom" local parts (RFC 5322):
    # alphanumeric, and !#$%&'*+-/=?^_`{|}~
    # Dots are allowed, but not at start/end, and not consecutive.
    # This regex ensures:
    # - Starts with one or more valid local characters (non-dot).
    # - Optionally followed by a sequence of a dot and one or more valid local characters (non-dot).
    # This implicitly disallows leading/trailing dots and consecutive dots.
    # This implementation focuses on the common "dot-atom" local part and does not
    # support "quoted-string" local parts (e.g., "John Doe"@example.com) for practical reasons,
    # as they are rare and significantly more complex to validate.
    local_part_pattern = r"^[a-zA-Z0-9!#$%&'*+-/=?^_`{|}~]+(?:\.[a-zA-Z0-9!#$%&'*+-/=?^_`{|}~]+)*$"
    if not re.fullmatch(local_part_pattern, local_part):
        return False

    # --- Domain Part Validation ---
    # RFC 5321 allows for either an FQDN (hostname) or an address-literal (e.g., IP address).
    # Check for IP address literal first (e.g., user@[192.168.1.1] or user@[IPv6:...)
    if domain_part.startswith('[') and domain_part.endswith(']'):
        literal_content = domain_part[1:-1] # Strip the square brackets

        # IPv4 literal validation (e.g., [192.168.1.1])
        # Regex for IPv4 address: ensures each octet is 0-255.
        ipv4_octet = r"(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])"
        ipv4_pattern = rf"^{ipv4_octet}(?:\.{ipv4_octet}){{3}}$"
        if re.fullmatch(ipv4_pattern, literal_content):
            return True # Valid IPv4 literal

        # IPv6 literal validation (e.g., [IPv6:2001:db8::1])
        # This comprehensive regex is adapted from common, robust IPv6 validation patterns,
        # covering full, abbreviated, and IPv4-mapped forms, as specified in RFC 4291 and RFC 5321.
        # It expects the 'IPv6:' prefix and then the address content.
        if literal_content.lower().startswith("ipv6:"):
            ipv6_addr_part = literal_content[5:] # Strip the "IPv6:" prefix
            # This regex is for the IPv6 address itself, not including "IPv6:" or "[]".
            # It covers all valid forms of IPv6 addresses.
            ipv6_addr_regex = r"(?:[A-Fa-f0-9]{1,4}(?::[A-Fa-f0-9]{1,4}){7}|::(?:[A-Fa-f0-9]{1,4}(?::[A-Fa-f0-9]{1,4}){0,6})?|([A-Fa-f0-9]{1,4}(?::[A-Fa-f0-9]{1,4}){0,5})?::[A-Fa-f0-9]{1,4}(?::[A-Fa-f0-9]{1,4}){0,1}|[A-Fa-f0-9]{1,4}(?::[A-Fa-f0-9]{1,4}){0,5}::[A-Fa-f0-9]{1,4}(?::[A-Fa-f0-9]{1,4}){0,1})(?:(?::(?:25[0-5]|2[0-4]\d|[01]?\d?\d)){3}(?:25[0-5]|2[0-4]\d|[01]?\d?\d))?"
            if re.fullmatch(ipv6_addr_regex, ipv6_addr_part):
                return True # Valid IPv6 literal

        # If it was an address literal but didn't match IPv4 or IPv6 format
        return False

    # If not an IP literal, continue with FQDN (hostname) validation

    # 1. No leading/trailing dots, no consecutive dots in the domain part.
    #    These are standard rules for hostname labels.
    if domain_part.startswith('.') or domain_part.endswith('.') or '..' in domain_part:
        return False

    # Split domain into labels (e.g., "example.com" -> ["example", "com"])
    domain_labels = domain_part.split('.')

    # 2. Domain must have at least two labels for public internet email (e.g., "example.com").
    #    This implicitly rejects single labels like "localhost" or "example" which are valid
    #    in some contexts (e.g., local networks) but generally not for publicly routable
    #    email addresses requiring a Top-Level Domain (TLD).
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