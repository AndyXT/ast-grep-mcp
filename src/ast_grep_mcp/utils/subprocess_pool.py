"""
Subprocess connection pooling for ast-grep commands.

This module provides a connection pool for managing ast-grep subprocess
instances to improve performance by reusing processes.
"""

import subprocess
import threading
import queue
import time
import logging
import os
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass
from contextlib import contextmanager

logger = logging.getLogger("ast_grep_mcp.subprocess_pool")


@dataclass
class PooledProcess:
    """Represents a pooled subprocess."""

    process: subprocess.Popen
    last_used: float
    in_use: bool = False
    created_at: float = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


class SubprocessPool:
    """
    Connection pool for ast-grep subprocesses.

    This pool manages a set of ast-grep processes that can be reused
    for multiple operations, reducing the overhead of process creation.
    """

    def __init__(
        self,
        min_size: int = 2,
        max_size: int = 10,
        max_idle_time: float = 300.0,  # 5 minutes
        ast_grep_path: str = "ast-grep",
    ):
        """
        Initialize the subprocess pool.

        Args:
            min_size: Minimum number of processes to maintain
            max_size: Maximum number of processes allowed
            max_idle_time: Maximum idle time before process is terminated
            ast_grep_path: Path to ast-grep executable
        """
        self.min_size = min_size
        self.max_size = max_size
        self.max_idle_time = max_idle_time
        self.ast_grep_path = ast_grep_path

        self._pool: List[PooledProcess] = []
        self._lock = threading.RLock()
        self._available = queue.Queue(maxsize=max_size)
        self._shutdown = False

        # Statistics
        self._stats = {
            "processes_created": 0,
            "processes_destroyed": 0,
            "commands_executed": 0,
            "pool_hits": 0,
            "pool_misses": 0,
        }

        # Start the pool maintenance thread
        self._maintenance_thread = threading.Thread(
            target=self._maintenance_loop, daemon=True
        )
        self._maintenance_thread.start()

        # Pre-create minimum processes
        self._ensure_minimum_processes()

    def _create_process(self) -> subprocess.Popen:
        """Create a new ast-grep process."""
        try:
            # Create process with pipes for communication
            process = subprocess.Popen(
                [self.ast_grep_path, "--json"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                env=os.environ.copy(),
            )

            self._stats["processes_created"] += 1
            logger.debug(f"Created new ast-grep process (PID: {process.pid})")
            return process

        except Exception as e:
            logger.error(f"Failed to create ast-grep process: {e}")
            raise

    def _ensure_minimum_processes(self):
        """Ensure minimum number of processes are available."""
        with self._lock:
            current_count = len(self._pool)
            needed = max(0, self.min_size - current_count)

            for _ in range(needed):
                try:
                    process = self._create_process()
                    pooled = PooledProcess(process=process, last_used=time.time())
                    self._pool.append(pooled)
                    self._available.put(pooled)
                except Exception as e:
                    logger.error(f"Failed to create minimum process: {e}")
                    break

    def _destroy_process(self, pooled: PooledProcess):
        """Safely destroy a pooled process."""
        try:
            if pooled.process.poll() is None:
                pooled.process.terminate()
                try:
                    pooled.process.wait(timeout=5.0)
                except subprocess.TimeoutExpired:
                    pooled.process.kill()
                    pooled.process.wait()

            self._stats["processes_destroyed"] += 1
            logger.debug(f"Destroyed ast-grep process (PID: {pooled.process.pid})")

        except Exception as e:
            logger.error(f"Error destroying process: {e}")

    def _maintenance_loop(self):
        """Background thread for pool maintenance."""
        while not self._shutdown:
            try:
                time.sleep(30)  # Check every 30 seconds
                self._cleanup_idle_processes()
                self._ensure_minimum_processes()
            except Exception as e:
                logger.error(f"Error in maintenance loop: {e}")

    def _cleanup_idle_processes(self):
        """Remove processes that have been idle too long."""
        with self._lock:
            current_time = time.time()
            to_remove = []

            for pooled in self._pool:
                if (
                    not pooled.in_use
                    and current_time - pooled.last_used > self.max_idle_time
                    and len(self._pool) > self.min_size
                ):
                    to_remove.append(pooled)

            for pooled in to_remove:
                self._pool.remove(pooled)
                self._destroy_process(pooled)
                logger.info(
                    f"Removed idle process (idle for {current_time - pooled.last_used:.1f}s)"
                )

    @contextmanager
    def get_process(self, timeout: float = 30.0):
        """
        Get a process from the pool.

        Args:
            timeout: Maximum time to wait for a process

        Yields:
            subprocess.Popen: A process from the pool
        """
        pooled = None
        start_time = time.time()

        try:
            # Try to get an available process
            try:
                pooled = self._available.get(timeout=timeout)
                self._stats["pool_hits"] += 1
            except queue.Empty:
                # No available process, create a new one if under limit
                with self._lock:
                    if len(self._pool) < self.max_size:
                        process = self._create_process()
                        pooled = PooledProcess(process=process, last_used=time.time())
                        self._pool.append(pooled)
                        self._stats["pool_misses"] += 1
                    else:
                        # Wait for a process to become available
                        wait_time = timeout - (time.time() - start_time)
                        if wait_time > 0:
                            pooled = self._available.get(timeout=wait_time)
                            self._stats["pool_hits"] += 1
                        else:
                            raise TimeoutError("No process available within timeout")

            # Mark process as in use
            with self._lock:
                pooled.in_use = True

            # Check if process is still alive
            if pooled.process.poll() is not None:
                # Process died, create a new one
                logger.warning("Process died, creating replacement")
                with self._lock:
                    self._pool.remove(pooled)
                process = self._create_process()
                pooled = PooledProcess(
                    process=process, last_used=time.time(), in_use=True
                )
                self._pool.append(pooled)

            yield pooled.process

        finally:
            # Return process to pool
            if pooled:
                with self._lock:
                    pooled.in_use = False
                    pooled.last_used = time.time()

                    # Check if process is still healthy
                    if pooled.process.poll() is None:
                        self._available.put(pooled)
                    else:
                        # Process died, remove from pool
                        logger.warning("Process died during use, removing from pool")
                        self._pool.remove(pooled)
                        self._ensure_minimum_processes()

    def execute_command(
        self, args: List[str], input_data: Optional[str] = None, timeout: float = 30.0
    ) -> Tuple[str, str, int]:
        """
        Execute an ast-grep command using a pooled process.

        Args:
            args: Command arguments (without 'ast-grep')
            input_data: Optional input to send to stdin
            timeout: Command execution timeout

        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        # For now, we'll use regular subprocess calls until we implement
        # a proper protocol for reusing ast-grep processes
        cmd = [self.ast_grep_path] + args

        try:
            result = subprocess.run(
                cmd,
                input=input_data,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=os.environ.copy(),
            )

            self._stats["commands_executed"] += 1
            return result.stdout, result.stderr, result.returncode

        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {' '.join(cmd)}")
            raise
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        with self._lock:
            stats = self._stats.copy()
            stats["current_pool_size"] = len(self._pool)
            stats["processes_in_use"] = sum(1 for p in self._pool if p.in_use)
            stats["processes_available"] = self._available.qsize()

            if self._stats["pool_hits"] + self._stats["pool_misses"] > 0:
                stats["hit_rate"] = self._stats["pool_hits"] / (
                    self._stats["pool_hits"] + self._stats["pool_misses"]
                )
            else:
                stats["hit_rate"] = 0.0

            return stats

    def shutdown(self):
        """Shutdown the pool and cleanup resources."""
        logger.info("Shutting down subprocess pool")
        self._shutdown = True

        # Destroy all processes
        with self._lock:
            for pooled in self._pool:
                self._destroy_process(pooled)
            self._pool.clear()

        # Clear the queue
        while not self._available.empty():
            try:
                self._available.get_nowait()
            except queue.Empty:
                break

        logger.info(f"Pool shutdown complete. Final stats: {self.get_stats()}")


# Global pool instance
_global_pool: Optional[SubprocessPool] = None
_pool_lock = threading.Lock()


def get_global_pool(**kwargs) -> SubprocessPool:
    """
    Get or create the global subprocess pool.

    Args:
        **kwargs: Arguments passed to SubprocessPool constructor

    Returns:
        The global SubprocessPool instance
    """
    global _global_pool

    with _pool_lock:
        if _global_pool is None:
            _global_pool = SubprocessPool(**kwargs)
            logger.info("Created global subprocess pool")

        return _global_pool


def shutdown_global_pool():
    """Shutdown the global pool if it exists."""
    global _global_pool

    with _pool_lock:
        if _global_pool is not None:
            _global_pool.shutdown()
            _global_pool = None
