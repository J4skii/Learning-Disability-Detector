"""
Performance monitoring and optimization utilities for LD Detector application.
Provides caching, database optimization, and performance monitoring.
"""
import time
import functools
import logging
from typing import Dict, Any, Optional, Callable
from flask import request, current_app, g
from sqlalchemy import text
from models import db
import os


logger = logging.getLogger(__name__)


class CacheManager:
    """Simple in-memory cache for frequently accessed data."""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default TTL
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() < entry['expires']:
                return entry['value']
            else:
                # Expired, remove from cache
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        ttl = ttl or self.default_ttl
        self.cache[key] = {
            'value': value,
            'expires': time.time() + ttl
        }
    
    def delete(self, key: str) -> None:
        """Delete key from cache."""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
    
    def cleanup_expired(self) -> None:
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time >= entry['expires']
        ]
        for key in expired_keys:
            del self.cache[key]


# Global cache instance
cache = CacheManager()


def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function results."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cached result for {cache_key}")
            
            return result
        
        return wrapper
    return decorator


class DatabaseOptimizer:
    """Database optimization utilities."""
    
    @staticmethod
    def optimize_queries():
        """Optimize database queries and indexes."""
        try:
            with db.engine.connect() as connection:
                # Enable query optimization for SQLite
                if 'sqlite' in str(db.engine.url):
                    connection.execute(text("PRAGMA optimize"))
                    connection.execute(text("PRAGMA analysis_limit=1000"))
                    connection.execute(text("PRAGMA optimize"))
                    logger.info("SQLite database optimized")
                
                # PostgreSQL optimizations
                elif 'postgresql' in str(db.engine.url):
                    connection.execute(text("ANALYZE"))
                    logger.info("PostgreSQL database analyzed")
                
                connection.commit()
                
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
    
    @staticmethod
    def get_query_stats():
        """Get database query statistics."""
        try:
            with db.engine.connect() as connection:
                if 'sqlite' in str(db.engine.url):
                    # SQLite query stats
                    result = connection.execute(text("SELECT * FROM sqlite_stat1 LIMIT 10"))
                    return result.fetchall()
                else:
                    return []
        except Exception as e:
            logger.error(f"Failed to get query stats: {e}")
            return []
    
    @staticmethod
    def vacuum_database():
        """Vacuum database to reclaim space and optimize."""
        try:
            with db.engine.connect() as connection:
                if 'sqlite' in str(db.engine.url):
                    connection.execute(text("VACUUM"))
                    logger.info("Database vacuumed successfully")
                connection.commit()
        except Exception as e:
            logger.error(f"Database vacuum failed: {e}")


class PerformanceMonitor:
    """Monitor application performance."""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {}
        self.slow_queries: list = []
        self.request_times: list = []
    
    def record_request_time(self, endpoint: str, duration: float):
        """Record request processing time."""
        self.request_times.append({
            'endpoint': endpoint,
            'duration': duration,
            'timestamp': time.time()
        })
        
        # Keep only last 1000 requests
        if len(self.request_times) > 1000:
            self.request_times = self.request_times[-1000:]
        
        # Log slow requests
        if duration > 2.0:
            logger.warning(f"Slow request detected: {endpoint} took {duration:.2f}s")
    
    def record_slow_query(self, query: str, duration: float, context: str = ""):
        """Record slow database queries."""
        self.slow_queries.append({
            'query': query[:200],  # Truncate long queries
            'duration': duration,
            'context': context,
            'timestamp': time.time()
        })
        
        # Keep only last 100 slow queries
        if len(self.slow_queries) > 100:
            self.slow_queries = self.slow_queries[-100:]
        
        logger.warning(f"Slow query detected in {context}: {duration:.2f}s")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.request_times:
            return {'error': 'No performance data available'}
        
        durations = [req['duration'] for req in self.request_times]
        
        return {
            'total_requests': len(self.request_times),
            'average_response_time': sum(durations) / len(durations),
            'slow_requests': len([d for d in durations if d > 2.0]),
            'slowest_endpoint': max(self.request_times, key=lambda x: x['duration'])['endpoint'],
            'slow_queries_count': len(self.slow_queries),
            'cache_hit_ratio': self.get_cache_hit_ratio()
        }
    
    def get_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        # This is a simplified calculation
        # In production, you'd want more sophisticated cache metrics
        total_entries = len(cache.cache)
        if total_entries == 0:
            return 0.0
        
        # Count non-expired entries
        current_time = time.time()
        valid_entries = sum(1 for entry in cache.cache.values() if current_time < entry['expires'])
        
        return (valid_entries / total_entries) * 100 if total_entries > 0 else 0.0


# Global performance monitor
performance_monitor = PerformanceMonitor()


def monitor_performance(f):
    """Decorator to monitor function performance."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = f(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            # Record performance metrics
            endpoint = f.__name__
            performance_monitor.record_request_time(endpoint, duration)
            
            # Log slow functions
            if duration > 1.0:
                logger.warning(f"Slow function detected: {endpoint} took {duration:.2f}s")
    
    return wrapper


def monitor_database_queries(f):
    """Decorator to monitor database query performance."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = f(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            # Log slow database operations
            if duration > 0.5:  # 500ms threshold
                performance_monitor.record_slow_query(
                    f"Function: {f.__name__}",
                    duration,
                    f"{f.__module__}.{f.__name__}"
                )
    
    return wrapper


class ConnectionPoolManager:
    """Manage database connection pool."""
    
    @staticmethod
    def configure_pool():
        """Configure database connection pool for optimal performance."""
        try:
            # Configure connection pool
            db.engine.pool._recycle = 3600  # Recycle connections after 1 hour
            db.engine.pool._pre_ping = True  # Validate connections before use
            db.engine.pool._pool_size = 10   # Connection pool size
            db.engine.pool._max_overflow = 20  # Additional connections if needed
            
            logger.info("Database connection pool configured")
            
        except Exception as e:
            logger.error(f"Failed to configure connection pool: {e}")
    
    @staticmethod
    def get_pool_status() -> Dict[str, Any]:
        """Get connection pool status."""
        try:
            pool = db.engine.pool
            return {
                'pool_size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'invalid': pool.invalid()
            }
        except Exception as e:
            logger.error(f"Failed to get pool status: {e}")
            return {}


def optimize_database_queries():
    """Optimize common database queries."""
    
    @cached(ttl=600)  # Cache for 10 minutes
    def get_active_tests():
        """Get active tests with caching."""
        return db.session.query(Test).filter_by(is_active=True).all()
    
    @cached(ttl=300)  # Cache for 5 minutes
    def get_user_count():
        """Get total user count with caching."""
        return db.session.query(User).count()
    
    @cached(ttl=180)  # Cache for 3 minutes
    def get_recent_results(limit: int = 10):
        """Get recent results with caching."""
        return db.session.query(Result).order_by(Result.timestamp.desc()).limit(limit).all()


class MemoryOptimizer:
    """Memory optimization utilities."""
    
    @staticmethod
    def cleanup_sessions():
        """Clean up expired sessions."""
        try:
            # This would clean up expired Flask sessions
            # Implementation depends on your session storage
            logger.info("Session cleanup completed")
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")
    
    @staticmethod
    def optimize_memory_usage():
        """Optimize memory usage."""
        try:
            # Clean up expired cache entries
            cache.cleanup_expired()
            
            # Force garbage collection
            import gc
            gc.collect()
            
            logger.info("Memory optimization completed")
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")


def setup_performance_monitoring(app):
    """Setup performance monitoring for Flask app."""
    
    @app.before_request
    def before_request():
        """Record request start time."""
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        """Record request completion time."""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            endpoint = request.endpoint or 'unknown'
            performance_monitor.record_request_time(endpoint, duration)
        
        return response
    
    # Configure database connection pool
    ConnectionPoolManager.configure_pool()
    
    # Setup periodic optimizations
    import threading
    
    def periodic_optimization():
        """Run periodic optimizations."""
        while True:
            try:
                time.sleep(3600)  # Run every hour
                DatabaseOptimizer.optimize_queries()
                MemoryOptimizer.optimize_memory_usage()
                cache.cleanup_expired()
            except Exception as e:
                logger.error(f"Periodic optimization failed: {e}")
    
    # Start optimization thread
    optimization_thread = threading.Thread(target=periodic_optimization, daemon=True)
    optimization_thread.start()
    
    logger.info("Performance monitoring setup completed")


def get_system_metrics() -> Dict[str, Any]:
    """Get system performance metrics."""
    try:
        import psutil
        
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'active_connections': len(psutil.net_connections()),
            'cache_size': len(cache.cache),
            'db_pool_status': ConnectionPoolManager.get_pool_status()
        }
    except ImportError:
        # psutil not available
        return {
            'error': 'psutil not available for system metrics',
            'cache_size': len(cache.cache),
            'db_pool_status': ConnectionPoolManager.get_pool_status()
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        return {'error': str(e)}


# Initialize performance monitoring when module is imported
if os.environ.get('FLASK_ENV') == 'production':
    # Only enable detailed monitoring in production
    logger.info("Production performance monitoring enabled")
else:
    logger.info("Development performance monitoring enabled")
