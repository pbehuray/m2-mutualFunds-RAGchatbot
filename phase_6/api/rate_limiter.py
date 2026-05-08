"""
Rate limiting implementation using in-memory storage.
For production, consider using Redis for distributed rate limiting.
"""

import time
from collections import defaultdict
from typing import Dict, Optional
from fastapi import Request, HTTPException


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, requests_per_minute: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute per IP
        """
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed.
        
        Args:
            identifier: Unique identifier (e.g., IP address)
            
        Returns:
            True if allowed, False otherwise
        """
        now = time.time()
        # Remove requests older than 1 minute
        self.requests[identifier] = [
            timestamp for timestamp in self.requests[identifier]
            if now - timestamp < 60
        ]
        
        # Check if under limit
        if len(self.requests[identifier]) < self.requests_per_minute:
            self.requests[identifier].append(now)
            return True
        
        return False
    
    def get_remaining_requests(self, identifier: str) -> int:
        """
        Get remaining requests for identifier.
        
        Args:
            identifier: Unique identifier
            
        Returns:
            Number of remaining requests
        """
        now = time.time()
        self.requests[identifier] = [
            timestamp for timestamp in self.requests[identifier]
            if now - timestamp < 60
        ]
        return max(0, self.requests_per_minute - len(self.requests[identifier]))


# Global rate limiter instance
rate_limiter = RateLimiter(requests_per_minute=60)


async def check_rate_limit(request: Request) -> None:
    """
    Check rate limit for request.
    
    Args:
        request: FastAPI request
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    client_ip = request.client.host if request.client else "unknown"
    
    if not rate_limiter.is_allowed(client_ip):
        remaining = rate_limiter.get_remaining_requests(client_ip)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again later. Remaining: {remaining}"
        )
