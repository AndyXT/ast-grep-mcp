"""
Real streaming implementation for large operations.
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import time
from dataclasses import dataclass, asdict
import queue
import threading
from enum import Enum

from ..utils.error_handling import handle_errors


class StreamStatus(Enum):
    INITIALIZING = "initializing"
    RUNNING = "running" 
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StreamChunk:
    """A chunk of streaming results."""
    chunk_id: int
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    is_final: bool = False
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass 
class StreamProgress:
    """Progress information for a stream."""
    total_items: int
    processed_items: int
    current_item: str
    elapsed_time: float
    estimated_remaining: float
    items_per_second: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class StreamingSearchEngine:
    """Real streaming search engine that processes files in chunks."""
    
    def __init__(self, analyzer=None, logger=None):
        self.analyzer = analyzer
        self.logger = logger
        self.active_streams = {}
        self.stream_counter = 0
    
    def create_search_stream(
        self,
        pattern: str,
        directory: str,
        language: Optional[str] = None,
        file_extensions: Optional[List[str]] = None,
        chunk_size: int = 10,
        max_workers: int = 2
    ) -> Dict[str, Any]:
        """
        Create a real streaming search that processes files in chunks.
        
        Args:
            pattern: AST pattern to search for
            directory: Directory to search
            language: Language filter
            file_extensions: File extension filter  
            chunk_size: Number of files per chunk
            max_workers: Number of parallel workers
            
        Returns:
            Stream configuration with stream_id
        """
        stream_id = f"stream_{self.stream_counter}_{int(time.time())}"
        self.stream_counter += 1
        
        # Discover all files to process
        dir_path = Path(directory)
        if not dir_path.exists():
            return {"error": f"Directory not found: {directory}"}
        
        files_to_process = []
        for file_path in dir_path.rglob("*"):
            if not file_path.is_file():
                continue
            
            # Apply file extension filter
            if file_extensions and file_path.suffix.lower() not in file_extensions:
                continue
            
            # Apply language filter  
            if language:
                detected_lang = self._detect_language(str(file_path))
                if detected_lang != language:
                    continue
            
            files_to_process.append(file_path)
        
        # Create stream state
        stream_state = {
            "stream_id": stream_id,
            "pattern": pattern,
            "directory": directory,
            "language": language,
            "file_extensions": file_extensions,
            "chunk_size": chunk_size,
            "max_workers": max_workers,
            "files_to_process": files_to_process,
            "total_files": len(files_to_process),
            "processed_files": 0,
            "status": StreamStatus.INITIALIZING,
            "results_queue": queue.Queue(),
            "start_time": time.time(),
            "current_chunk": 0,
            "total_chunks": (len(files_to_process) + chunk_size - 1) // chunk_size,
            "error": None,
            "progress": None
        }
        
        self.active_streams[stream_id] = stream_state
        
        # Start processing in background thread
        threading.Thread(
            target=self._process_stream,
            args=(stream_id,),
            daemon=True
        ).start()
        
        return {
            "stream_id": stream_id,
            "status": "created",
            "total_files": len(files_to_process),
            "total_chunks": stream_state["total_chunks"],
            "chunk_size": chunk_size,
            "usage": {
                "get_next_chunk": f"get_stream_chunk('{stream_id}')",
                "get_progress": f"get_stream_progress('{stream_id}')",
                "cancel_stream": f"cancel_stream('{stream_id}')"
            }
        }
    
    def get_stream_chunk(self, stream_id: str, timeout: float = 30.0) -> Dict[str, Any]:
        """Get the next chunk of results from a stream."""
        if stream_id not in self.active_streams:
            return {"error": f"Stream not found: {stream_id}"}
        
        stream_state = self.active_streams[stream_id]
        
        try:
            # Wait for next chunk
            chunk = stream_state["results_queue"].get(timeout=timeout)
            
            # Update progress
            progress = self._calculate_progress(stream_state)
            
            response = {
                "stream_id": stream_id,
                "chunk": chunk.to_dict(),
                "progress": progress.to_dict(),
                "status": stream_state["status"].value,
                "has_more": not chunk.is_final and stream_state["status"] != StreamStatus.COMPLETED
            }
            
            # Clean up completed streams
            if chunk.is_final:
                self._cleanup_stream(stream_id)
            
            return response
            
        except queue.Empty:
            # Timeout - check if stream is still active
            if stream_state["status"] in [StreamStatus.COMPLETED, StreamStatus.FAILED, StreamStatus.CANCELLED]:
                return {
                    "stream_id": stream_id,
                    "chunk": None,
                    "status": stream_state["status"].value,
                    "has_more": False,
                    "error": stream_state.get("error")
                }
            else:
                return {
                    "stream_id": stream_id,
                    "chunk": None,
                    "status": stream_state["status"].value,
                    "has_more": True,
                    "message": "No data available yet, try again"
                }
    
    def get_stream_progress(self, stream_id: str) -> Dict[str, Any]:
        """Get current progress of a stream."""
        if stream_id not in self.active_streams:
            return {"error": f"Stream not found: {stream_id}"}
        
        stream_state = self.active_streams[stream_id]
        progress = self._calculate_progress(stream_state)
        
        return {
            "stream_id": stream_id,
            "progress": progress.to_dict(),
            "status": stream_state["status"].value,
            "error": stream_state.get("error")
        }
    
    def cancel_stream(self, stream_id: str) -> Dict[str, Any]:
        """Cancel an active stream."""
        if stream_id not in self.active_streams:
            return {"error": f"Stream not found: {stream_id}"}
        
        stream_state = self.active_streams[stream_id]
        stream_state["status"] = StreamStatus.CANCELLED
        
        return {
            "stream_id": stream_id,
            "status": "cancelled",
            "message": "Stream cancellation requested"
        }
    
    def list_active_streams(self) -> Dict[str, Any]:
        """List all active streams."""
        streams = []
        for stream_id, state in self.active_streams.items():
            progress = self._calculate_progress(state)
            streams.append({
                "stream_id": stream_id,
                "pattern": state["pattern"],
                "directory": state["directory"],
                "status": state["status"].value,
                "progress": progress.to_dict()
            })
        
        return {
            "active_streams": streams,
            "total_active": len(streams)
        }
    
    def _process_stream(self, stream_id: str):
        """Process a stream in background thread."""
        stream_state = self.active_streams[stream_id]
        
        try:
            stream_state["status"] = StreamStatus.RUNNING
            
            files_to_process = stream_state["files_to_process"]
            chunk_size = stream_state["chunk_size"]
            pattern = stream_state["pattern"]
            
            # Process files in chunks
            for chunk_idx in range(0, len(files_to_process), chunk_size):
                # Check for cancellation
                if stream_state["status"] == StreamStatus.CANCELLED:
                    break
                
                chunk_files = files_to_process[chunk_idx:chunk_idx + chunk_size]
                chunk_results = []
                
                # Process each file in the chunk
                for file_path in chunk_files:
                    if stream_state["status"] == StreamStatus.CANCELLED:
                        break
                    
                    try:
                        result = self._process_single_file(file_path, pattern)
                        if result:
                            chunk_results.append(result)
                        
                        stream_state["processed_files"] += 1
                        
                    except Exception as e:
                        if self.logger:
                            self.logger.debug(f"Error processing {file_path}: {e}")
                        continue
                
                # Create chunk
                chunk_num = chunk_idx // chunk_size
                is_final = (chunk_idx + chunk_size) >= len(files_to_process)
                
                chunk = StreamChunk(
                    chunk_id=chunk_num,
                    data=chunk_results,
                    metadata={
                        "chunk_size": len(chunk_results),
                        "files_processed": len(chunk_files),
                        "chunk_number": chunk_num + 1,
                        "total_chunks": stream_state["total_chunks"]
                    },
                    is_final=is_final
                )
                
                # Add chunk to queue
                stream_state["results_queue"].put(chunk)
                stream_state["current_chunk"] = chunk_num
                
                # Small delay to prevent overwhelming
                time.sleep(0.1)
            
            # Mark as completed if not cancelled
            if stream_state["status"] != StreamStatus.CANCELLED:
                stream_state["status"] = StreamStatus.COMPLETED
                
        except Exception as e:
            stream_state["status"] = StreamStatus.FAILED
            stream_state["error"] = str(e)
            
            # Add error chunk
            error_chunk = StreamChunk(
                chunk_id=-1,
                data=[],
                metadata={},
                is_final=True,
                error=str(e)
            )
            stream_state["results_queue"].put(error_chunk)
    
    def _process_single_file(self, file_path: Path, pattern: str) -> Optional[Dict[str, Any]]:
        """Process a single file for matches."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Detect language
            language = self._detect_language(str(file_path))
            if not language:
                return None
            
            # Use analyzer if available
            if self.analyzer:
                result = self.analyzer.analyze_code(content, language, pattern)
                if result and result.get("matches"):
                    return {
                        "file": str(file_path),
                        "language": language,
                        "matches": len(result["matches"]),
                        "sample_matches": result["matches"][:3],  # First 3 matches only
                        "file_size": len(content),
                        "lines": content.count('\n') + 1
                    }
            else:
                # Simple fallback
                if pattern in content:
                    import re
                    matches = list(re.finditer(re.escape(pattern), content))
                    if matches:
                        return {
                            "file": str(file_path),
                            "language": language,
                            "matches": len(matches),
                            "file_size": len(content),
                            "lines": content.count('\n') + 1
                        }
        
        except Exception:
            pass
        
        return None
    
    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect language from file extension."""
        ext = Path(file_path).suffix.lower()
        extension_map = {
            ".py": "python",
            ".rs": "rust",
            ".js": "javascript",
            ".jsx": "javascript", 
            ".ts": "typescript",
            ".tsx": "typescript",
            ".go": "go",
            ".c": "c",
            ".h": "c",
            ".cpp": "cpp",
            ".java": "java",
            ".lua": "lua",
        }
        return extension_map.get(ext)
    
    def _calculate_progress(self, stream_state: Dict) -> StreamProgress:
        """Calculate current progress for a stream."""
        total_files = stream_state["total_files"]
        processed_files = stream_state["processed_files"]
        elapsed_time = time.time() - stream_state["start_time"]
        
        if processed_files > 0 and elapsed_time > 0:
            items_per_second = processed_files / elapsed_time
            estimated_remaining = (total_files - processed_files) / items_per_second if items_per_second > 0 else 0
        else:
            items_per_second = 0
            estimated_remaining = 0
        
        current_item = f"Processing chunk {stream_state['current_chunk'] + 1}/{stream_state['total_chunks']}"
        
        return StreamProgress(
            total_items=total_files,
            processed_items=processed_files,
            current_item=current_item,
            elapsed_time=elapsed_time,
            estimated_remaining=estimated_remaining,
            items_per_second=items_per_second
        )
    
    def _cleanup_stream(self, stream_id: str):
        """Clean up completed stream."""
        if stream_id in self.active_streams:
            # Keep stream state for a short time in case of late requests
            threading.Timer(300.0, lambda: self.active_streams.pop(stream_id, None)).start()


class StreamingSecurityAuditor:
    """Streaming security auditor for large codebases."""
    
    def __init__(self, search_engine: StreamingSearchEngine):
        self.search_engine = search_engine
        
        # Security patterns by language
        self.security_patterns = {
            "rust": [
                {"pattern": "unwrap()", "severity": "medium", "issue": "Potential panic"},
                {"pattern": "expect($MSG)", "severity": "medium", "issue": "Potential panic"},
                {"pattern": "unsafe { $$$CODE }", "severity": "high", "issue": "Unsafe code block"},
                {"pattern": "ptr::$FUNC", "severity": "high", "issue": "Raw pointer operations"},
            ],
            "python": [
                {"pattern": "eval($CODE)", "severity": "high", "issue": "Code injection risk"},
                {"pattern": "exec($CODE)", "severity": "high", "issue": "Code injection risk"},
                {"pattern": "subprocess.call($$$ARGS, shell=True)", "severity": "high", "issue": "Shell injection risk"},
                {"pattern": "open($FILE, 'w')", "severity": "low", "issue": "File write without checks"},
            ],
            "javascript": [
                {"pattern": "eval($CODE)", "severity": "high", "issue": "Code injection risk"},
                {"pattern": "innerHTML = $VAL", "severity": "medium", "issue": "XSS risk"},
                {"pattern": "document.write($VAL)", "severity": "medium", "issue": "XSS risk"},
            ]
        }
    
    @handle_errors
    def run_security_audit_streaming(
        self,
        directory: str,
        language: str,
        chunk_size: int = 5,
        severity_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run security audit with streaming results.
        
        Args:
            directory: Directory to audit
            language: Primary language to audit
            chunk_size: Files per chunk
            severity_filter: Filter by severity levels
            
        Returns:
            Stream configuration for security audit
        """
        if language not in self.security_patterns:
            return {"error": f"Security patterns not available for language: {language}"}
        
        # Get patterns for language
        patterns = self.security_patterns[language]
        if severity_filter:
            patterns = [p for p in patterns if p["severity"] in severity_filter]
        
        # Create composite stream that searches for multiple patterns
        stream_results = []
        
        for pattern_info in patterns:
            stream_result = self.search_engine.create_search_stream(
                pattern=pattern_info["pattern"],
                directory=directory,
                language=language,
                chunk_size=chunk_size
            )
            
            if "error" not in stream_result:
                stream_result["pattern_info"] = pattern_info
                stream_results.append(stream_result)
        
        return {
            "audit_type": "security_streaming",
            "language": language,
            "directory": directory,
            "pattern_streams": stream_results,
            "total_patterns": len(patterns),
            "usage": {
                "get_results": "Use get_security_audit_results() to collect results from all streams",
                "monitor": "Use get_audit_progress() to monitor overall progress"
            }
        }