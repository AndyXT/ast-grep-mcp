"""
Streaming response utilities for handling large result sets.

This module provides functionality to stream results for large-scale
pattern searches, preventing memory issues and improving responsiveness.
"""

import asyncio
import logging
from typing import AsyncIterator, Dict, Any, List, Optional, Callable
from pathlib import Path
from dataclasses import dataclass
import json

logger = logging.getLogger("ast_grep_mcp.streaming")


@dataclass
class StreamConfig:
    """Configuration for streaming responses."""

    batch_size: int = 100  # Number of files to process in each batch
    max_results_per_file: int = 1000  # Maximum results per file before truncation
    enable_progress: bool = True  # Whether to include progress updates
    memory_limit_mb: int = 512  # Memory limit for buffering results


class ResultStreamer:
    """Handles streaming of search results for large operations."""

    def __init__(self, config: Optional[StreamConfig] = None):
        """
        Initialize the result streamer.

        Args:
            config: Streaming configuration
        """
        self.config = config or StreamConfig()
        self._cancel_event = asyncio.Event()

    async def stream_directory_search(
        self,
        directory: Path,
        pattern: str,
        language: str,
        file_handler: Callable[[Path, str, str], List[Dict[str, Any]]],
        file_filter: Optional[Callable[[Path], bool]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream search results from a directory.

        Args:
            directory: Directory to search
            pattern: Pattern to search for
            language: Programming language
            file_handler: Function to process each file
            file_filter: Optional function to filter files

        Yields:
            Dictionary with batch results or progress updates
        """
        # Get all matching files
        all_files = []
        extensions = self._get_extensions_for_language(language)

        for ext in extensions:
            files = list(directory.rglob(f"*{ext}"))
            if file_filter:
                files = [f for f in files if file_filter(f)]
            all_files.extend(files)

        total_files = len(all_files)
        if total_files == 0:
            yield {
                "type": "complete",
                "total_files": 0,
                "total_matches": 0,
                "message": "No files found matching criteria",
            }
            return

        # Process files in batches
        processed_files = 0
        total_matches = 0

        for batch_start in range(0, total_files, self.config.batch_size):
            if self._cancel_event.is_set():
                yield {
                    "type": "cancelled",
                    "processed_files": processed_files,
                    "total_matches": total_matches,
                }
                return

            batch_end = min(batch_start + self.config.batch_size, total_files)
            batch_files = all_files[batch_start:batch_end]

            # Process batch
            batch_results = {}
            batch_matches = 0

            for file_path in batch_files:
                try:
                    # Read file content
                    content = file_path.read_text(encoding="utf-8", errors="ignore")

                    # Process file
                    matches = file_handler(file_path, content, pattern)

                    if matches:
                        # Limit results per file if needed
                        if len(matches) > self.config.max_results_per_file:
                            matches = matches[: self.config.max_results_per_file]
                            truncated = True
                        else:
                            truncated = False

                        batch_results[str(file_path)] = {
                            "matches": matches,
                            "count": len(matches),
                            "truncated": truncated,
                        }
                        batch_matches += len(matches)

                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    batch_results[str(file_path)] = {
                        "error": str(e),
                        "matches": [],
                        "count": 0,
                    }

            processed_files += len(batch_files)
            total_matches += batch_matches

            # Yield batch result
            yield {
                "type": "batch",
                "batch_number": batch_start // self.config.batch_size + 1,
                "files": batch_results,
                "batch_match_count": batch_matches,
                "progress": {
                    "processed_files": processed_files,
                    "total_files": total_files,
                    "percentage": (processed_files / total_files) * 100,
                    "total_matches": total_matches,
                },
            }

        # Final summary
        yield {
            "type": "complete",
            "total_files": total_files,
            "total_matches": total_matches,
            "processed_files": processed_files,
        }

    async def stream_large_file_search(
        self,
        file_path: Path,
        pattern: str,
        language: str,
        line_handler: Callable[[str, int, str], Optional[Dict[str, Any]]],
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream search results from a large file.

        Args:
            file_path: Path to the large file
            pattern: Pattern to search for
            language: Programming language
            line_handler: Function to process each line

        Yields:
            Dictionary with batch results or progress updates
        """
        try:
            file_size = file_path.stat().st_size
            processed_bytes = 0
            line_number = 0
            batch_matches = []
            total_matches = 0

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                while True:
                    if self._cancel_event.is_set():
                        yield {
                            "type": "cancelled",
                            "processed_lines": line_number,
                            "total_matches": total_matches,
                        }
                        return

                    # Read chunk of lines
                    lines = []
                    chunk_size = 0

                    for _ in range(1000):  # Process 1000 lines at a time
                        line = f.readline()
                        if not line:
                            break
                        lines.append(line)
                        chunk_size += len(line.encode("utf-8"))
                        line_number += 1

                    if not lines:
                        break

                    # Process lines
                    for i, line in enumerate(lines):
                        match = line_handler(
                            line, line_number - len(lines) + i + 1, pattern
                        )
                        if match:
                            batch_matches.append(match)

                    processed_bytes += chunk_size

                    # Yield batch if we have enough matches
                    if len(batch_matches) >= self.config.batch_size:
                        total_matches += len(batch_matches)
                        yield {
                            "type": "batch",
                            "file": str(file_path),
                            "matches": batch_matches,
                            "batch_match_count": len(batch_matches),
                            "progress": {
                                "processed_lines": line_number,
                                "processed_bytes": processed_bytes,
                                "total_bytes": file_size,
                                "percentage": (processed_bytes / file_size) * 100,
                                "total_matches": total_matches,
                            },
                        }
                        batch_matches = []

            # Yield remaining matches
            if batch_matches:
                total_matches += len(batch_matches)
                yield {
                    "type": "batch",
                    "file": str(file_path),
                    "matches": batch_matches,
                    "batch_match_count": len(batch_matches),
                    "progress": {
                        "processed_lines": line_number,
                        "processed_bytes": processed_bytes,
                        "total_bytes": file_size,
                        "percentage": 100.0,
                        "total_matches": total_matches,
                    },
                }

            # Final summary
            yield {
                "type": "complete",
                "file": str(file_path),
                "total_lines": line_number,
                "total_matches": total_matches,
                "file_size_bytes": file_size,
            }

        except Exception as e:
            logger.error(f"Error streaming file {file_path}: {e}")
            yield {"type": "error", "file": str(file_path), "error": str(e)}

    def cancel(self):
        """Cancel ongoing streaming operation."""
        self._cancel_event.set()

    def reset(self):
        """Reset the streamer for a new operation."""
        self._cancel_event.clear()

    def _get_extensions_for_language(self, language: str) -> List[str]:
        """Get file extensions for a language."""
        extension_map = {
            "python": [".py"],
            "javascript": [".js", ".jsx"],
            "typescript": [".ts", ".tsx"],
            "rust": [".rs"],
            "go": [".go"],
            "c": [".c", ".h"],
            "lua": [".lua"],
        }
        return extension_map.get(language, [])


class StreamingSearchHandler:
    """Handler for streaming search operations in the MCP server."""

    def __init__(self, analyzer):
        """
        Initialize the streaming handler.

        Args:
            analyzer: The AstAnalyzer instance
        """
        self.analyzer = analyzer
        self.streamer = ResultStreamer()

    async def search_directory_streaming(
        self, directory: str, pattern: str, language: str, include_progress: bool = True
    ) -> AsyncIterator[str]:
        """
        Search directory with streaming JSON responses.

        Args:
            directory: Directory path to search
            pattern: Pattern to search for
            language: Programming language
            include_progress: Whether to include progress updates

        Yields:
            JSON-encoded result batches
        """
        dir_path = Path(directory)

        if not dir_path.exists() or not dir_path.is_dir():
            yield json.dumps(
                {"type": "error", "error": f"Directory not found: {directory}"}
            )
            return

        # Configure streaming
        self.streamer.config.enable_progress = include_progress

        # Define file handler
        def process_file(
            file_path: Path, content: str, pattern: str
        ) -> List[Dict[str, Any]]:
            """Process a single file."""
            return self.analyzer.find_patterns(content, language, pattern)

        # Stream results
        async for result in self.streamer.stream_directory_search(
            dir_path, pattern, language, process_file
        ):
            yield json.dumps(result) + "\n"

    async def search_large_file_streaming(
        self, file_path: str, pattern: str, language: str
    ) -> AsyncIterator[str]:
        """
        Search a large file with streaming JSON responses.

        Args:
            file_path: Path to the file
            pattern: Pattern to search for
            language: Programming language

        Yields:
            JSON-encoded result batches
        """
        path = Path(file_path)

        if not path.exists() or not path.is_file():
            yield json.dumps({"type": "error", "error": f"File not found: {file_path}"})
            return

        # For now, use regular search since line-by-line doesn't work well with AST
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            matches = self.analyzer.find_patterns(content, language, pattern)

            # Stream results in batches
            batch_size = 100
            total_matches = len(matches)

            for i in range(0, total_matches, batch_size):
                batch = matches[i : i + batch_size]
                yield json.dumps(
                    {
                        "type": "batch",
                        "file": file_path,
                        "matches": batch,
                        "batch_match_count": len(batch),
                        "progress": {
                            "processed_matches": min(i + batch_size, total_matches),
                            "total_matches": total_matches,
                            "percentage": min(
                                (i + batch_size) / total_matches * 100, 100
                            ),
                        },
                    }
                ) + "\n"

            yield json.dumps(
                {"type": "complete", "file": file_path, "total_matches": total_matches}
            ) + "\n"

        except Exception as e:
            yield json.dumps(
                {"type": "error", "file": file_path, "error": str(e)}
            ) + "\n"
