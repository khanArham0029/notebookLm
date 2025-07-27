import jwt
import os
from typing import Dict, Any
from supabase import create_client, Client
from fastapi import HTTPException
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class AuthService:
    def __init__(self):
        self.supabase_url =os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
        
        logger.debug(f"[AuthService Init] SUPABASE_URL: {self.supabase_url}")
        logger.debug(f"[AuthService Init] SUPABASE_SERVICE_ROLE_KEY (first 5 chars): {self.supabase_key[:5] if self.supabase_key else 'None'}")
        logger.debug(f"[AuthService Init] SUPABASE_JWT_SECRET (first 5 chars): {self.jwt_secret[:5] if self.jwt_secret else 'None'}")
        
        if not all([self.supabase_url, self.supabase_key, self.jwt_secret]):
            raise ValueError("Missing required Supabase environment variables")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token and return user info"""
        try:
            # Decode the JWT token
            issuer = f"{self.supabase_url}/auth/v1"
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"],audience="authenticated",issuer=issuer)
            user_id = payload.get("sub")
            
            logger.debug(f"[verify_token] Decoded JWT payload: {payload}")
            
            if not user_id:
                logger.error("[verify_token] JWT payload missing 'sub' (user ID)")
                raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
            
            # Get user info from Supabase using the provided token
            # This validates the token against Supabase's auth system
            user_response = self.supabase.auth.get_user(token)
            
            logger.debug(f"[verify_token] Supabase get_user response: {user_response}")

            if user_response.user:
                logger.info(f"[verify_token] User authenticated: {user_response.user.id}")
                return {
                    "id": user_response.user.id,
                    "email": user_response.user.email,
                    "user_metadata": user_response.user.user_metadata
                }
            else:
                logger.error(f"[verify_token] Supabase get_user returned no user. Error: {user_response.error}")
                raise HTTPException(status_code=401, detail="User not found or token invalid with Supabase")
                
        except jwt.ExpiredSignatureError:
            logger.error("[verify_token] Token expired")
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            logger.error(f"[verify_token] Invalid token: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger.error(f"[verify_token] Authentication error: {e}", exc_info=True)
            raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")