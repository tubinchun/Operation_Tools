try:
    from .auth_service import AuthService
except ImportError:
    AuthService = None

__all__ = ['AuthService']
