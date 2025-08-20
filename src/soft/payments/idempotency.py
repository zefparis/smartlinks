"""Idempotency guard using Redis."""

import os
import json
import hashlib
from typing import Any, Dict, Optional
from functools import wraps
# import redis.asyncio as redis  # Temporarily disabled
from fastapi import HTTPException, Request
import logging

logger = logging.getLogger(__name__)

# Redis client for idempotency (disabled for now)
_redis_client = None

async def get_redis_client():
    """Get Redis client for idempotency (disabled)."""
    return None

def generate_idempotency_key(data: Dict[str, Any]) -> str:
    """Generate idempotency key from request data."""
    # Sort keys for consistent hashing
    sorted_data = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(sorted_data.encode()).hexdigest()

async def check_idempotency(key: str, ttl_seconds: int = 3600) -> Optional[Dict[str, Any]]:
    """Check if operation was already performed (disabled without Redis)."""
    return None

async def store_idempotency_result(key: str, result: Dict[str, Any], ttl_seconds: int = 3600):
    """Store operation result for idempotency (disabled without Redis)."""
    pass

def guard(operation_prefix: str, ttl_seconds: int = 3600):
    """Decorator for idempotency guard."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request data for idempotency key
            request_data = {}
            
            # Look for request body in kwargs
            for arg in args:
                if hasattr(arg, 'json'):  # FastAPI Request
                    try:
                        body = await arg.json()
                        request_data.update(body)
                    except:
                        pass
                elif isinstance(arg, dict):
                    request_data.update(arg)
            
            for key, value in kwargs.items():
                if isinstance(value, dict):
                    request_data.update(value)
                else:
                    request_data[key] = value
            
            # Generate idempotency key
            idempotency_key = f"{operation_prefix}:{generate_idempotency_key(request_data)}"
            
            # Check if already processed
            existing_result = await check_idempotency(idempotency_key, ttl_seconds)
            if existing_result:
                logger.info(f"Returning cached result for {idempotency_key}")
                return existing_result
            
            # Execute operation
            result = await func(*args, **kwargs)
            
            # Store result for future idempotency checks
            if isinstance(result, dict):
                await store_idempotency_result(idempotency_key, result, ttl_seconds)
            
            return result
        
        return wrapper
    return decorator
