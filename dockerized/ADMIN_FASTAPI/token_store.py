#!/usr/bin/env python3
# Author: skondla@me.com
# Purpose: Server-side token state — JWT denylist (revocation), refresh-token
#          family rotation with reuse detection, and distributed rate-limit
#          counters. Backed by Redis when REDIS_URL is set (shared across all
#          replicas); falls back to a thread-safe in-process store otherwise.
# -*- coding: utf-8 -*-

import logging
import os
import threading
import time
from typing import Optional

logger = logging.getLogger("security")

_REFRESH_FAMILY_PREFIX = "jwt:family:"
_DENYLIST_PREFIX = "jwt:deny:"
_RATELIMIT_PREFIX = "rl:"


class MemoryTokenStore:
    """In-process fallback store. Correct for a single replica; per-pod only
    when the deployment scales out — use Redis (REDIS_URL) in production so
    revocation and rate limits are global."""

    def __init__(self):
        self._data: dict[str, tuple[str, float]] = {}
        self._counters: dict[str, tuple[int, float]] = {}
        self._lock = threading.Lock()

    def _purge(self) -> None:
        now = time.time()
        expired = [k for k, (_, exp) in self._data.items() if exp <= now]
        for k in expired:
            del self._data[k]

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        with self._lock:
            self._purge()
            self._data[key] = (value, time.time() + ttl_seconds)

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            item = self._data.get(key)
            if not item:
                return None
            value, exp = item
            if exp <= time.time():
                del self._data[key]
                return None
            return value

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def incr_window(self, key: str, window_seconds: int) -> int:
        """Fixed-window counter: returns the count for the current window."""
        now = time.time()
        with self._lock:
            count, reset_at = self._counters.get(key, (0, now + window_seconds))
            if reset_at <= now:
                count, reset_at = 0, now + window_seconds
            count += 1
            self._counters[key] = (count, reset_at)
            return count


class RedisTokenStore:
    """Redis-backed store shared by every replica."""

    def __init__(self, url: str):
        import redis  # imported lazily so the app runs without the package

        self._client = redis.Redis.from_url(url, decode_responses=True,
                                            socket_timeout=2, socket_connect_timeout=2)
        self._client.ping()

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        self._client.set(key, value, ex=max(ttl_seconds, 1))

    def get(self, key: str) -> Optional[str]:
        return self._client.get(key)

    def delete(self, key: str) -> None:
        self._client.delete(key)

    def incr_window(self, key: str, window_seconds: int) -> int:
        pipe = self._client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds, nx=True)
        count, _ = pipe.execute()
        return int(count)


_store = None
_store_lock = threading.Lock()


def get_token_store():
    """Process-wide store singleton. Redis when REDIS_URL is set, else memory."""
    global _store
    if _store is not None:
        return _store
    with _store_lock:
        if _store is not None:
            return _store
        url = os.environ.get("REDIS_URL", "").strip()
        if url:
            try:
                _store = RedisTokenStore(url)
                logger.info("Token store: Redis (%s)", url.split("@")[-1])
                return _store
            except Exception as exc:
                logger.error("Token store: Redis unavailable (%s) — falling back "
                             "to in-process store. Revocation and rate limits are "
                             "per-pod until Redis recovers.", exc)
        else:
            logger.warning("Token store: REDIS_URL not set — using in-process "
                           "store (per-pod revocation/rate limits).")
        _store = MemoryTokenStore()
        return _store


# ─── JWT denylist (server-side revocation) ────────────────────────────────────

def denylist_jti(jti: str, ttl_seconds: int) -> None:
    """Revoke a token by jti until it would have expired anyway."""
    get_token_store().set(_DENYLIST_PREFIX + jti, "1", ttl_seconds)


def is_denylisted(jti: str) -> bool:
    return get_token_store().get(_DENYLIST_PREFIX + jti) is not None


# ─── Refresh-token families (rotation + reuse detection) ──────────────────────

def register_refresh(family_id: str, jti: str, ttl_seconds: int) -> None:
    """Record `jti` as the one currently-valid refresh token of this family."""
    get_token_store().set(_REFRESH_FAMILY_PREFIX + family_id, jti, ttl_seconds)


def rotate_refresh(family_id: str, presented_jti: str, new_jti: str,
                   ttl_seconds: int) -> bool:
    """Atomically-enough rotate a refresh family.

    Returns True when `presented_jti` is the family's current token (normal
    rotation). Returns False on reuse — a previously-rotated token was
    replayed — in which case the whole family is revoked.
    """
    store = get_token_store()
    current = store.get(_REFRESH_FAMILY_PREFIX + family_id)
    if current is None or current != presented_jti:
        # Reuse (or unknown family): kill the chain so the thief's copy dies too.
        store.delete(_REFRESH_FAMILY_PREFIX + family_id)
        logger.warning("Refresh-token reuse detected for family=%s — family revoked",
                       family_id)
        return False
    store.set(_REFRESH_FAMILY_PREFIX + family_id, new_jti, ttl_seconds)
    return True


def revoke_family(family_id: str) -> None:
    get_token_store().delete(_REFRESH_FAMILY_PREFIX + family_id)


def is_family_active(family_id: str, jti: str) -> bool:
    return get_token_store().get(_REFRESH_FAMILY_PREFIX + family_id) == jti


# ─── Distributed rate limiting ────────────────────────────────────────────────

def rate_limit_hit(key: str, limit: int, window_seconds: int) -> bool:
    """Count a request against `key`; True when the caller is over the limit."""
    count = get_token_store().incr_window(_RATELIMIT_PREFIX + key, window_seconds)
    return count > limit
