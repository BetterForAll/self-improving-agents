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
    # RFC 5321 specifies a maximum total length of 255 characters (including dots) for a domain name.
    if len(domain_part) > 255:
        return False

    # --- Local Part Validation ---
    # Allowed characters: alphanumeric, and !#$%&'*+-/=?^_`{|}~ (RFC 5322 atext)
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
    # Check for address literal (e.g., [192.168.1.1] or [IPv6:...]) as per RFC 5321.
    if domain_part.startswith('[') and domain_part.endswith(']'):
        literal = domain_part[1:-1] # Remove brackets
        
        # Regex for four octets separated by dots. Each octet must be 0-255.
        ipv4_pattern_bare = r"(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
        
        # 1. IPv4 literal check (e.g., 192.168.1.1)
        if re.fullmatch(ipv4_pattern_bare, literal):
            return True # Valid IPv4 literal domain
        
        # 2. IPv6 literal check (e.g., IPv6:2001:db8::1)
        # This regex is a relatively comprehensive pattern for IPv6 addresses as string literals.
        # It covers full addresses, addresses with '::' compression, and embedded IPv4.
        # This pattern is adapted from various reliable sources (e.g., Django's validator, common RFC interpretations).
        ipv6_pattern_address_part = (
            r"(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|"                                   # Full form (8 hex groups)
            r"(?:[0-9a-fA-F]{1,4}:){1,7}:|"                                                # Compressed at end (1-7 hex groups then '::')
            r":(?::[0-9a-fA-F]{1,4}){1,7}|"                                                # Compressed at start ('::' then 1-7 hex groups)
            r"(?:[0-9a-fA-F]{1,4}:){1,6}:" + ipv4_pattern_bare + r"|"                       # Embedded IPv4 (6 hex groups then ':' then IPv4)
            r"::(?:[0-9a-fA-F]{1,4}:){0,5}" + ipv4_pattern_bare + r"|"                      # Embedded IPv4 ('::' then 0-5 hex groups then ':' then IPv4)
            r"(?:[0-9a-fA-F]{1,4}:){1,5}::(?:[0-9a-fA-F]{1,4}:){0,4}" + ipv4_pattern_bare + r"|" # Embedded IPv4 (1-5 hex groups then '::' then 0-4 hex groups then ':' then IPv4)
            r"(?:[0-9a-fA-F]{1,4}:){1,6}[0-9a-fA-F]{1,4}|"                                 # Other compressed forms (e.g., a:b::c:d)
            r"(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|"
            r"(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|"
            r"(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|"
            r"(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|"
            r"[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})?|"                           # Single hex group then optional '::' and 1-6 hex groups
            r"::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}|"                               # '::' and 0-6 hex groups then single hex group
            r"::"                                                                           # Just '::'
        )
        if re.fullmatch(r"^IPv6:" + ipv6_pattern_address_part + r"$", literal):
            return True
            
        return False # Not a valid domain literal (neither IPv4 nor IPv6)

    # If it's not a domain literal, proceed with hostname validation.
    # 1. No leading/trailing dots, no consecutive dots in the domain part.
    if domain_part.startswith('.') or domain_part.endswith('.') or '..' in domain_part:
        return False

    # Split domain into labels (e.g., "example.com" -> ["example", "com"])
    domain_labels = domain_part.split('.')

    # A domain must have at least one label. This is implicitly handled if domain_part is not empty.
    # The `if not label:` check handles empty labels resulting from '..' or leading/trailing dots.

    # 3. Validate each label in the domain part
    for label in domain_labels:
        if not label: # Empty label (e.g., "example..com" would result in an empty string in labels)
            return False
        if len(label) > 63: # Each label max 63 characters (RFC 1035)
            return False
        # Each label must start and end with an alphanumeric character.
        # Can contain alphanumeric characters or hyphens in between.
        # This regex strictly follows RFC 1035/1123 for hostname labels.
        # It also implicitly disallows a label consisting only of a hyphen.
        label_pattern = r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$"
        if not re.fullmatch(label_pattern, label):
            return False

    # Relaxed hostname validation: Removed the requirement for a minimum of two labels
    # (allowing single-label domains like 'user@localhost') and removed the minimum TLD length.
    # The character and length validation for all labels (including the TLD) are already
    # handled by the loop and `label_pattern`.

    return True