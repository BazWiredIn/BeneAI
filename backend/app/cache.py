"""Simple in-memory cache for advice"""

import time
import hashlib
import json
from typing import Optional
from .config import settings


class AdviceCache:
    def __init__(self):
        self.cache = {}
        self.enabled = settings.cache_enabled
        self.ttl = settings.cache_ttl_seconds
        self.max_size = settings.cache_max_size

    def get_cache_key(self, parameters: dict) -> str:
        """Generate cache key from parameters"""

        # Extract relevant fields for caching
        emotion = parameters["emotion"]["label"]
        wpm = parameters["speech"]["wordsPerMinute"]
        filler_count = parameters["speech"]["fillerWords"]["total"]

        # Round WPM to buckets of 20
        wpm_bucket = (wpm // 20) * 20

        # Filler count buckets (0-5, 6-10, 11+)
        filler_bucket = min(filler_count // 5, 2) * 5

        # Create key
        key_data = {
            "emotion": emotion,
            "wpm_bucket": wpm_bucket,
            "filler_bucket": filler_bucket
        }

        # Hash key
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, parameters: dict) -> Optional[str]:
        """Get cached advice if available"""

        if not self.enabled:
            return None

        key = self.get_cache_key(parameters)

        if key in self.cache:
            entry = self.cache[key]

            # Check if expired
            if time.time() - entry["timestamp"] < self.ttl:
                print(f"Cache hit for key: {key}")
                return entry["advice"]
            else:
                # Remove expired entry
                del self.cache[key]

        return None

    def set(self, parameters: dict, advice: str):
        """Cache advice"""

        if not self.enabled:
            return

        key = self.get_cache_key(parameters)

        # Enforce max size
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]

        # Store
        self.cache[key] = {
            "advice": advice,
            "timestamp": time.time()
        }

        print(f"Cached advice for key: {key}")

    def clear(self):
        """Clear all cached entries"""
        self.cache = {}
        print("Cache cleared")

    def stats(self) -> dict:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "enabled": self.enabled
        }


# Global cache instance
advice_cache = AdviceCache()
