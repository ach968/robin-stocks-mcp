# robin_stocks_mcp/robinhood/client.py
import os
import json
from typing import Optional
from pathlib import Path
import robin_stocks.robinhood as rh
from .errors import AuthRequiredError, RobinhoodAPIError, NetworkError


class RobinhoodClient:
    """Manages Robinhood authentication and session state."""
    
    def __init__(self):
        self._authenticated = False
        self._username: Optional[str] = None
        self._password: Optional[str] = None
        self._session_path: Optional[str] = None
        self._allow_mfa: bool = False
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment."""
        self._username = os.getenv('RH_USERNAME')
        self._password = os.getenv('RH_PASSWORD')
        self._session_path = os.getenv('RH_SESSION_PATH')
        self._allow_mfa = os.getenv('RH_ALLOW_MFA', '0') == '1'
    
    def _load_session(self) -> bool:
        """Load cached session if available."""
        if not self._session_path:
            return False
        
        session_file = Path(self._session_path)
        if not session_file.exists():
            return False
        
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            # Try to use the session token
            # robin_stocks stores session internally, we just check if it's valid
            return self._is_session_valid()
        except Exception:
            return False
    
    def _save_session(self):
        """Save current session to disk."""
        if not self._session_path:
            return
        
        try:
            session_file = Path(self._session_path)
            session_file.parent.mkdir(parents=True, exist_ok=True)
            # robin_stocks manages the session internally
            # We just track that we have one
            with open(session_file, 'w') as f:
                json.dump({'authenticated': True}, f)
        except Exception:
            pass  # Don't fail if we can't save session
    
    def _is_session_valid(self) -> bool:
        """Check if current session is valid."""
        try:
            # Try a simple API call that requires auth
            account = rh.load_account_profile()
            return account is not None
        except Exception:
            return False
    
    def ensure_session(self, mfa_code: Optional[str] = None) -> 'RobinhoodClient':
        """Ensure we have a valid session, authenticating if needed.
        
        Raises:
            AuthRequiredError: If authentication is required but not possible.
        """
        if self._authenticated and self._is_session_valid():
            return self
        
        # Try to load cached session
        if self._load_session() and self._is_session_valid():
            self._authenticated = True
            return self
        
        # Need to authenticate
        if not self._username or not self._password:
            raise AuthRequiredError(
                "Authentication required. Please set RH_USERNAME and RH_PASSWORD, "
                "or ensure a valid session cache exists. You may need to refresh "
                "your session in the Robinhood app."
            )
        
        try:
            login_result = rh.login(
                self._username,
                self._password,
                mfa_code=mfa_code if self._allow_mfa else None,
                store_session=True
            )
            
            if login_result:
                self._authenticated = True
                self._save_session()
                return self
            else:
                raise AuthRequiredError(
                    "Login failed. Please check your credentials or refresh "
                    "your session in the Robinhood app."
                )
        except Exception as e:
            if "challenge" in str(e).lower():
                raise AuthRequiredError(
                    "Authentication challenge required. Please refresh your "
                    "session in the Robinhood app, or enable MFA fallback with "
                    "RH_ALLOW_MFA=1 and provide mfa_code."
                )
            raise NetworkError(f"Failed to authenticate: {e}")
    
    def logout(self):
        """Clear session."""
        try:
            rh.logout()
        except Exception:
            pass
        self._authenticated = False
        if self._session_path:
            try:
                Path(self._session_path).unlink(missing_ok=True)
            except Exception:
                pass
