class DomainException(Exception):
    """Base exception for all domain-level errors."""
    pass

class QuotaExceededException(DomainException):
    """Raised when a tenant exceeds their plan limits."""
    pass

class ResourceNotFoundException(DomainException):
    """Raised when a requested domain entity is not found."""
    pass

class InvalidOperationException(DomainException):
    """Raised when an operation cannot be performed in the current state."""
    pass

class AuthenticationException(DomainException):
    """Raised when API Key or other authentication fails at the domain level."""
    pass
