import secrets
import string

_ALPHABET = string.ascii_letters + string.digits


def generate_ref_code(length: int = 8) -> str:
    """Generate a random referral code."""
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


def roll_dice() -> int:
    """Return a cryptographically secure random integer between 1 and 6 (inclusive),
    used for the dice game so outcomes are fair and unpredictable."""
    return secrets.randbelow(6) + 1
