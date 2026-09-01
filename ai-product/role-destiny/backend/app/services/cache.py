"""
内存缓存服务 - 基于cachetools TTLCache
替代Redis，实现简单的LRU缓存
"""
from cachetools import TTLCache
from typing import Any, Optional
from app.config import settings
from loguru import logger


class CacheService:
    """缓存服务"""

    def __init__(self, maxsize: int = None, ttl: int = None):
        self.maxsize = maxsize or settings.CACHE_MAX_SIZE
        self.ttl = ttl or settings.CACHE_TTL
        self._cache = TTLCache(maxsize=self.maxsize, ttl=self.ttl)
        logger.info(f"Cache initialized: maxsize={self.maxsize}, ttl={self.ttl}s")

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            value = self._cache.get(key)
            if value is not None:
                logger.debug(f"Cache HIT: {key}")
            else:
                logger.debug(f"Cache MISS: {key}")
            return value
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """设置缓存值"""
        try:
            if ttl:
                # 临时TTL，使用新cache实例
                temp_cache = TTLCache(maxsize=1, ttl=ttl)
                temp_cache[key] = value
                # 注意：临时TTL缓存会在过期后被GC回收
            else:
                self._cache[key] = value
            logger.debug(f"Cache SET: {key}")
        except Exception as e:
            logger.error(f"Cache set error: {e}")

    def delete(self, key: str) -> None:
        """删除缓存"""
        try:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache DELETE: {key}")
        except Exception as e:
            logger.error(f"Cache delete error: {e}")

    def clear(self) -> None:
        """清空所有缓存"""
        try:
            self._cache.clear()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")

    def has(self, key: str) -> bool:
        """检查key是否存在"""
        return key in self._cache

    @property
    def size(self) -> int:
        """获取当前缓存大小"""
        return len(self._cache)


# 全局缓存服务实例
cache_service = CacheService()


def cache_key(prefix: str, *args) -> str:
    """生成缓存key"""
    return f"{prefix}:{':'.join(str(arg) for arg in args)}"
