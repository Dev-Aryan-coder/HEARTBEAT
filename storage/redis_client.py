import redis
import logging
from heartbeat.config import get_config

# Configure logging
logger = logging.getLogger("HEARTBEAT_REDIS")

class RedisClient:
    """ISSUE 7.1 FIX: Centralized Redis Singleton."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            config = get_config()
            logger.info(f"Connecting to Redis at {config.redis_host}:{config.redis_port}...")
            # Create the instance
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance.connection = redis.Redis(
                host=config.redis_host,
                port=config.redis_port,
                decode_responses=True,
                socket_timeout=5,
                retry_on_timeout=True
            )
            try:
                cls._instance.connection.ping()
                logger.info("Redis Connection Established.")
            except Exception as e:
                logger.error(f"Redis Connection Failed: {str(e)}")
                # Allow instance to be created but log the failure
                # Consumers should handle redis errors gracefully
        return cls._instance

    @property
    def r(self):
        """Standard property to access the connection."""
        return self.connection

def get_redis_client() -> redis.Redis:
    """Returns the shared Redis connection."""
    return RedisClient().r
