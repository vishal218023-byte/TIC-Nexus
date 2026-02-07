"""Authentication and authorization utilities."""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User

# Security configuration
SECRET_KEY = "BEL-TLC-NEXUS-SECRET-KEY-CHANGE-IN-PRODUCTION"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using bcrypt directly."""
    import bcrypt
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        # Fallback to passlib for backwards compatibility with old hashes
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except:
            return False


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt directly."""
    import bcrypt
    # Bcrypt has a 72 byte limit, truncate if necessary
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, username: str, password: str):
    """Authenticate a user by username and password."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    if not user.is_active:
        return False
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Verify that the current user has admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def get_current_librarian_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """Verify that the current user has librarian or admin role."""
    if current_user.role not in ["admin", "librarian"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Librarian or Admin privileges required"
        )
    return current_user


async def get_user_from_token_query(
    token: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get user from token passed as query parameter (for iframe/file viewing)."""
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    
    user = db.query(User).filter(User.username == username).first()
    return user


async def get_current_user_optional(
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get the current user if authenticated, None otherwise (for public endpoints)."""
    from fastapi import Request
    from starlette.requests import Request as StarletteRequest
    
    # Try to get token from Authorization header
    try:
        token = await oauth2_scheme(None)
        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                username: str = payload.get("sub")
                if username:
                    user = db.query(User).filter(User.username == username).first()
                    return user
            except JWTError:
                pass
    except:
        pass
    
    return None


# Custom OAuth2 scheme that doesn't auto-redirect (for HTML pages)
class OAuth2PasswordBearerCookie(OAuth2PasswordBearer):
    """OAuth2 scheme that checks both Authorization header and doesn't raise on missing token."""
    
    async def __call__(self, request: Request) -> Optional[str]:
        """Extract token from Authorization header, return None if not found."""
        authorization: str = request.headers.get("Authorization")
        if authorization:
            scheme, _, param = authorization.partition(" ")
            if scheme.lower() == "bearer":
                return param
        return None


oauth2_scheme_optional = OAuth2PasswordBearerCookie(tokenUrl="api/auth/login", auto_error=False)


async def get_current_user_optional_for_pages(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get the current authenticated user if token is provided, None otherwise.
    
    This is used for HTML page routes. The actual authentication check 
    will be done client-side via JavaScript checking localStorage.
    This function is kept for potential server-side validation in API calls.
    """
    # Try to get token from Authorization header
    authorization: str = request.headers.get("Authorization")
    token = None
    
    if authorization:
        scheme, _, param = authorization.partition(" ")
        if scheme.lower() == "bearer":
            token = param
    
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    
    user = db.query(User).filter(User.username == username).first()
    return user
