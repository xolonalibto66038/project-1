# apps/authentication/exceptions.py


class RoleRequiredException(Exception):
    """Raised when a user attempts to login without a role assigned."""

    pass
