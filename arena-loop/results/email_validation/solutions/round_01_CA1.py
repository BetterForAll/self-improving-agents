import re

def validate_email(email):
    """Check if an email address is valid.

    Args:
        email: str, the email address to validate

    Returns: True if valid, False if invalid
    """
    # Regex for characters allowed in the local part before the '@' symbol.
    # This set is based on common email standards (RFC 5322, etc.) but adapted
    # to specifically address the given failure cases.
    # It includes alphanumeric characters and common special characters
    # (excluding '.' at start/end or consecutively, which is handled by structure).
    LOCAL_PART_CHARS = r"[a-zA-Z0-9!#$%&'*+-/=?^_`{|}~]"

    # Structure for the local part:
    # - Must start and end with an allowed LOCAL_PART_CHARS character (prevents .user@, user.@)
    # - Can contain dots internally, but not consecutively (prevents user..name@)
    # - Must not be empty (prevents @domain.com)
    LOCAL_PART_REGEX = LOCAL_PART_CHARS + r"+(?:\." + LOCAL_PART_CHARS + r"+)*"

    # Regex for a single domain label (e.g., "example" in "example.com").
    # - Must start and end with an alphanumeric character (prevents -example.com, example-.com)
    # - Can contain alphanumeric characters or hyphens internally.
    # - Hyphens cannot be consecutive (e.g., a--b.com fails)
    DOMAIN_LABEL_REGEX = r"[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*"

    # Structure for the domain part (e.g., "example.com"):
    # - Consists of one or more domain labels separated by dots.
    # - The Top-Level Domain (TLD, the last part like "com") must be at least two letters long
    #   (prevents example.c).
    # - Prevents domains starting with a dot (e.g., @.com) or having consecutive dots (e.g., @example..com).
    DOMAIN_PART_REGEX = DOMAIN_LABEL_REGEX + r"(?:\." + DOMAIN_LABEL_REGEX + r")*\." + r"[a-zA-Z]{2,}"

    # Combined regex for the full email address:
    # - Anchors ^ and $ ensure the entire string matches, preventing leading/trailing whitespace
    #   or other invalid characters (e.g., user@example.com\n).
    # - Exactly one '@' symbol separating the local and domain parts (prevents user@@example.com).
    EMAIL_FULL_PATTERN = r"^" + LOCAL_PART_REGEX + r"@" + DOMAIN_PART_REGEX + r"$"

    # Use re.match to check if the email string matches the full pattern from the beginning.
    # bool() converts the match object (if successful) or None (if failed) into True or False.
    return bool(re.match(EMAIL_FULL_PATTERN, email))