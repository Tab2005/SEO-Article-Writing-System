"""
User Service.

Business logic for user management.
"""

from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import get_password_hash, verify_password, PasswordValidator
from app.core.exceptions import ConflictException, BadRequestException, NotFoundException
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Service for user management operations."""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, user_data: UserCreate) -> User:
        """
        Create a new user.
        
        Args:
            db: Database session
            user_data: User creation data
            
        Returns:
            Created user
            
        Raises:
            ConflictException: If email already exists
            BadRequestException: If password doesn't meet requirements
        """
        # Validate password strength
        is_valid, errors = PasswordValidator.validate(user_data.password)
        if not is_valid:
            raise BadRequestException("; ".join(errors))
        
        # Check if email exists
        existing = await UserService.get_by_email(db, user_data.email)
        if existing:
            raise ConflictException("Email already registered")
        
        # Create user
        user = User(
            email=user_data.email.lower(),
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
        )
        
        db.add(user)
        await db.flush()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def authenticate(
        db: AsyncSession,
        email: str,
        password: str,
    ) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Args:
            db: Database session
            email: User email
            password: User password
            
        Returns:
            User if authentication successful, None otherwise
        """
        user = await UserService.get_by_email(db, email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    @staticmethod
    async def update(
        db: AsyncSession,
        user: User,
        user_data: UserUpdate,
    ) -> User:
        """
        Update user profile.
        
        Args:
            db: Database session
            user: User to update
            user_data: Update data
            
        Returns:
            Updated user
        """
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        
        if user_data.email is not None:
            # Check if new email is already taken
            existing = await UserService.get_by_email(db, user_data.email)
            if existing and existing.id != user.id:
                raise ConflictException("Email already in use")
            user.email = user_data.email.lower()
        
        await db.flush()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def change_password(
        db: AsyncSession,
        user: User,
        current_password: str,
        new_password: str,
    ) -> bool:
        """
        Change user password.
        
        Args:
            db: Database session
            user: User to update
            current_password: Current password for verification
            new_password: New password
            
        Returns:
            True if successful
            
        Raises:
            BadRequestException: If current password is wrong or new password is weak
        """
        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise BadRequestException("Current password is incorrect")
        
        # Validate new password strength
        is_valid, errors = PasswordValidator.validate(new_password)
        if not is_valid:
            raise BadRequestException("; ".join(errors))
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        await db.flush()
        
        return True
    
    @staticmethod
    async def update_last_login(db: AsyncSession, user: User) -> None:
        """Update user's last login timestamp."""
        user.last_login = datetime.now(timezone.utc)
        await db.flush()


# Singleton instance
user_service = UserService()
