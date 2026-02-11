# robin_stocks_mcp/robinhood/client.py
import logging
import os
from typing import Optional
from pathlib import Path
import robin_stocks.robinhood as rh
from .errors import AuthRequiredError, NetworkError

logger = logging.getLogger(__name__)

# robin_stocks stores sessions as pickle files.
# Default location: ~/.tokens/robinhood.pickle
# With pickle_path: {pickle_path}/robinhood.pickle
# With pickle_name: {pickle_path}/robinhood{pickle_name}.pickle
_PICKLE_FILENAME = "robinhood.pickle"


class RobinhoodClient:
    """Manages Robinhood authentication and session state.

    Session persistence is delegated entirely to robin_stocks, which uses
    pickle files. When ``session_path`` is provided it is forwarded as
    ``pickle_path`` to ``rh.login()`` so the pickle is stored in the
    requested directory.

    Args take priority over environment variables.
    """

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        session_path: Optional[str] = None,
        allow_mfa: Optional[bool] = None,
    ):
        self._authenticated = False
        self._username = username or os.getenv("RH_USERNAME")
        self._password = password or os.getenv("RH_PASSWORD")
        self._session_path = session_path or os.getenv("RH_SESSION_PATH")
        self._allow_mfa = (
            allow_mfa
            if allow_mfa is not None
            else os.getenv("RH_ALLOW_MFA", "0") == "1"
        )

    def ensure_session(self, mfa_code: Optional[str] = None) -> "RobinhoodClient":
        """Ensure we have a valid session, authenticating if needed.

        Delegates session caching and validation to ``robin_stocks``.
        ``rh.login()`` will automatically restore a cached pickle session
        (validating it against the positions endpoint) before falling back
        to a fresh login.

        Raises:
            AuthRequiredError: If authentication is required but not possible.
        """
        if self._authenticated:
            logger.debug("Session already active, skipping login")
            return self

        if not self._username or not self._password:
            logger.warning("Authentication failed: missing credentials")
            raise AuthRequiredError(
                "Authentication required. Please set RH_USERNAME and RH_PASSWORD, "
                "or ensure a valid session cache exists. You may need to refresh "
                "your session in the Robinhood app."
            )

        try:
            login_kwargs: dict = {
                "username": self._username,
                "password": self._password,
                "store_session": True,
            }

            if self._session_path:
                login_kwargs["pickle_path"] = self._session_path

            if self._allow_mfa and mfa_code:
                login_kwargs["mfa_code"] = mfa_code

            logger.info("Authenticating user %s", self._username)
            logger.debug(
                "Login kwargs: store_session=%s, pickle_path=%s, mfa=%s",
                login_kwargs.get("store_session"),
                login_kwargs.get("pickle_path"),
                "provided" if login_kwargs.get("mfa_code") else "none",
            )
            login_result = rh.login(**login_kwargs)

            if login_result:
                self._authenticated = True
                logger.info("Authentication successful for user %s", self._username)
                return self
            else:
                logger.warning("Authentication failed for user %s", self._username)
                raise AuthRequiredError(
                    "Login failed. Please check your credentials or refresh "
                    "your session in the Robinhood app."
                )
        except AuthRequiredError:
            raise
        except Exception as e:
            if "challenge" in str(e).lower():
                logger.warning("Authentication challenge required for user %s", self._username)
                raise AuthRequiredError(
                    "Authentication challenge required. Please refresh your "
                    "session in the Robinhood app, or enable MFA fallback with "
                    "RH_ALLOW_MFA=1 and provide mfa_code."
                )
            logger.warning("Authentication error: %s", e)
            raise NetworkError(f"Failed to authenticate: {e}")

    def logout(self):
        """Clear session and remove cached pickle file."""
        logger.debug("Logging out and clearing session")
        try:
            rh.logout()
        except Exception:
            pass
        self._authenticated = False
        # robin_stocks.logout() only clears in-memory state.
        # Also remove the persisted pickle file so next start is clean.
        if self._session_path:
            try:
                pickle_file = Path(self._session_path) / _PICKLE_FILENAME
                pickle_file.unlink(missing_ok=True)
            except Exception:
                pass
