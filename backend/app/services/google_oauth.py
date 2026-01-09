"""
Google OAuth Service.

Handles Google OAuth authentication flow.
"""

from typing import Optional
import httpx

from app.config import settings
from app.core.exceptions import ExternalServiceException, UnauthorizedException


class GoogleOAuthService:
    """Service for Google OAuth authentication."""
    
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def verify_google_token(self, access_token: str) -> dict:
        """
        Verify Google access token and get user info.
        
        Args:
            access_token: Google OAuth access token
            
        Returns:
            User info dict with id, email, name, picture
        """
        try:
            client = await self._get_client()
            response = await client.get(
                self.GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            
            if response.status_code != 200:
                raise UnauthorizedException("Invalid Google token")
            
            data = response.json()
            
            return {
                "google_id": data.get("id"),
                "email": data.get("email"),
                "name": data.get("name"),
                "picture": data.get("picture"),
                "verified_email": data.get("verified_email", False),
            }
            
        except httpx.RequestError as e:
            raise ExternalServiceException(f"Failed to verify Google token: {e}")
    
    async def exchange_code_for_token(
        self,
        code: str,
        redirect_uri: str,
        client_id: str,
        client_secret: str,
    ) -> dict:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from Google
            redirect_uri: Redirect URI used in authorization
            client_id: Google OAuth client ID
            client_secret: Google OAuth client secret
            
        Returns:
            Token response with access_token, refresh_token, etc.
        """
        try:
            client = await self._get_client()
            response = await client.post(
                self.GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            
            if response.status_code != 200:
                raise UnauthorizedException("Failed to exchange code for token")
            
            return response.json()
            
        except httpx.RequestError as e:
            raise ExternalServiceException(f"Failed to exchange code: {e}")


# Singleton instance
google_oauth_service = GoogleOAuthService()
