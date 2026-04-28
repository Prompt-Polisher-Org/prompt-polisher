from passlib.context import CryptContext

# bcrypt is intentionally slow — if an attacker steals your DB,
# it would take them YEARS to crack bcrypt hashes vs seconds for MD5
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a plain text password matches the stored hash.
    Used during login: user sends "mypassword123",
    we compare it against the hash stored in the database.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password. NEVER store plain text passwords in the database.
    Used during registration: user sends "mypassword123",
    we store "$2b$12$LJ3m4ys..." in the database.
    """
    return pwd_context.hash(password)