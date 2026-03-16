# robin_stocks_mcp/robinhood/errors.py
class RobinhoodError(Exception):
    """Base error for Robinhood operations."""

    pass


class AuthRequiredError(RobinhoodError):
    """Raised when authentication is required but unavailable."""

    pass


class InvalidArgumentError(RobinhoodError):
    """Raised when tool input is invalid."""

    pass


class RobinhoodAPIError(RobinhoodError):
    """Raised when Robinhood API returns an error."""

    pass


class NetworkError(RobinhoodError):
    """Raised when network operations fail."""

    pass
