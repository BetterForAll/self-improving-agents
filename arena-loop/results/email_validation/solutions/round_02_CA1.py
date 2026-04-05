import re

def validate_email(email):
    """Check if an email address is valid.

    Args:
        email: str, the email address to validate

    Returns: True if valid, False if invalid
    """
    # Regex for characters allowed in the unquoted local part before the '@' symbol.
    # This set is based on common email standards (RFC 5322, etc.).
    # It includes alphanumeric characters and common special characters (excluding '.' and '"').
    LOCAL_ATOM_CHARS = r"[a-zA-Z0-9!#$%&'*+-/=?^_`{|}~]"

    # Structure for the unquoted local part:
    # - Must start and end with an allowed LOCAL_ATOM_CHARS character (prevents .user@, user.@)
    # - Can contain dots internally, but not consecutively (prevents user..name@)
    # - Must not be empty.
    UNQUOTED_LOCAL_PART_REGEX = LOCAL_ATOM_CHARS + r"+(?:\." + LOCAL_ATOM_CHARS + r"+)*"

    # Regex for content inside a quoted local part (e.g., "first last", "a@b", ".localpart.").
    # Allows any character except backslash or double quote, OR an escaped character (e.g., \\, \").
    # This simplified version allows more characters than RFC 5322 qtext for practical validation,
    # specifically to allow '@' and ' ' directly inside, and '.' at boundaries.
    QUOTED_STRING_CHAR = r"(?:[^\"\\]|\\.)" # Any char except " or \ , OR an escaped char
    
    # Structure for a quoted local part: starts with ", ends with ", contains QUOTED_STRING_CHAR.
    # Allows empty quoted strings (e.g., ""@domain.com) which are RFC-compliant.
    QUOTED_LOCAL_PART_REGEX = r"\"" + QUOTED_STRING_CHAR + r"*\""

    # Combined local part regex: either an unquoted string or a quoted string.
    LOCAL_PART_REGEX = f"(?:{UNQUOTED_LOCAL_PART_REGEX}|{QUOTED_LOCAL_PART_REGEX})"

    # Regex for a single domain label (e.g., "example" in "example.com").
    # - Must start and end with an alphanumeric character (prevents -example.com, example-.com)
    # - Can contain alphanumeric characters or hyphens internally.
    # - Hyphens cannot be consecutive (e.g., a--b.com fails)
    HOSTNAME_LABEL_REGEX = r"[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*"

    # Structure for the hostname part of the domain (e.g., "example.com"):
    # - Consists of one or more domain labels separated by dots.
    # - The Top-Level Domain (TLD, the last part like "com") must be at least two letters long
    #   (prevents example.c).
    HOSTNAME_DOMAIN_REGEX = HOSTNAME_LABEL_REGEX + r"(?:\." + HOSTNAME_LABEL_REGEX + r")*\." + r"[a-zA-Z]{2,}"

    # Regex for a single IPv4 octet (0-255).
    IP_OCTET = r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
    # Regex for a full IPv4 address string (e.g., 192.168.1.1).
    IPv4_ADDRESS_STR_REGEX = IP_OCTET + r"\." + IP_OCTET + r"\." + IP_OCTET + r"\." + IP_OCTET
    # Structure for an IP address literal domain (e.g., [192.168.1.1]).
    IPv4_LITERAL_REGEX = r"\[" + IPv4_ADDRESS_STR_REGEX + r"\]"

    # Combined domain part regex: either a standard hostname, a numeric IPv4 address string, or an IPv4 literal.
    # This covers cases like "example.com", "123.123.123.123", and "[192.168.1.1]".
    DOMAIN_PART_REGEX = f"(?:{HOSTNAME_DOMAIN_REGEX}|{IPv4_ADDRESS_STR_REGEX}|{IPv4_LITERAL_REGEX})"

    # Combined regex for the full email address:
    # - Exactly one '@' symbol separating the local and domain parts.
    EMAIL_FULL_PATTERN = LOCAL_PART_REGEX + r"@" + DOMAIN_PART_REGEX

    # Use re.fullmatch to check if the entire email string matches the pattern.
    # This ensures no leading/trailing whitespace or other invalid characters (e.g., user@example.com\n).
    # bool() converts the match object (if successful) or None (if failed) into True or False.
    return bool(re.fullmatch(EMAIL_FULL_PATTERN, email))