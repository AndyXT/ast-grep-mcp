"""
Benchmarking utilities for ast-grep-mcp.

This module provides functions for benchmarking the performance of ast-grep-mcp.
"""

import time
import statistics
from typing import Callable, Dict, Any, List, Tuple, Optional
import logging
from pathlib import Path
import os
import tempfile
import random
import string
from ..ast_analyzer import AstAnalyzer

logger = logging.getLogger("ast_grep_mcp.benchmarks")


class Benchmark:
    """Benchmark class for measuring performance."""

    def __init__(self, name: str, iterations: int = 5):
        """
        Initialize a benchmark.

        Args:
            name: Benchmark name
            iterations: Number of iterations to run
        """
        self.name = name
        self.iterations = iterations
        self.results: Dict[str, List[float]] = {}

    def measure(self, func: Callable, *args, **kwargs) -> Tuple[float, Any]:
        """
        Measure the execution time of a function.

        Args:
            func: Function to measure
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            Tuple of (execution time in seconds, function result)
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        return elapsed, result

    def run_benchmark(
        self, label: str, func: Callable, *args, **kwargs
    ) -> Tuple[List[float], List[Any]]:
        """
        Run a benchmark multiple times and collect results.

        Args:
            label: Label for this benchmark run
            func: Function to benchmark
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            Tuple of (list of execution times, list of function results)
        """
        times = []
        results = []

        # Prepare log messages once outside the loop
        total_iterations = self.iterations
        iteration_template = (
            f"Running {label} - iteration {{current}}/{total_iterations}"
        )
        result_template = f"{label} - iteration {{current}}: {{elapsed:.4f}}s"

        for i in range(total_iterations):
            current_iteration = i + 1
            logger.info(iteration_template.format(current=current_iteration))

            elapsed, result = self.measure(func, *args, **kwargs)
            times.append(elapsed)
            results.append(result)

            logger.info(
                result_template.format(current=current_iteration, elapsed=elapsed)
            )

        self.results[label] = times
        return times, results

    def get_stats(self, label: Optional[str] = None) -> Dict[str, Dict[str, float]]:
        """
        Get statistics for benchmark results.

        Args:
            label: Optional label to get stats for (if None, get stats for all)

        Returns:
            Dictionary with statistics for each benchmark
        """
        stats = {}

        labels = [label] if label else self.results.keys()

        for lbl in labels:
            if lbl not in self.results:
                continue

            times = self.results[lbl]
            stats[lbl] = {
                "min": min(times),
                "max": max(times),
                "mean": statistics.mean(times),
                "median": statistics.median(times),
                "stdev": statistics.stdev(times) if len(times) > 1 else 0,
            }

        return stats

    def compare(self, baseline_label: str, optimized_label: str) -> Dict[str, Any]:
        """
        Compare two benchmark results and calculate the speedup.

        Args:
            baseline_label: Label for the baseline benchmark
            optimized_label: Label for the optimized benchmark

        Returns:
            Dictionary with comparison results
        """
        if baseline_label not in self.results or optimized_label not in self.results:
            return {"error": "Labels not found in results"}

        baseline_stats = self.get_stats(baseline_label)[baseline_label]
        optimized_stats = self.get_stats(optimized_label)[optimized_label]

        # Calculate speedup ratio
        speedup = baseline_stats["mean"] / optimized_stats["mean"]
        percentage = (speedup - 1) * 100

        return {
            "baseline": baseline_stats,
            "optimized": optimized_stats,
            "speedup_ratio": speedup,
            "speedup_percentage": percentage,
            "time_saved": baseline_stats["mean"] - optimized_stats["mean"],
        }

    def print_results(self) -> None:
        """Print benchmark results."""
        logger.info(f"=== {self.name} Benchmark Results ===")

        # Calculate statistics once for all labels
        stats_dict = self.get_stats()

        # Print results for each label using the pre-calculated stats
        for label, stats in stats_dict.items():
            logger.info(f"{label}:")
            logger.info(f"  Min: {stats['min']:.4f}s")
            logger.info(f"  Max: {stats['max']:.4f}s")
            logger.info(f"  Mean: {stats['mean']:.4f}s")
            logger.info(f"  Median: {stats['median']:.4f}s")
            logger.info(f"  StdDev: {stats['stdev']:.4f}s")


def create_synthetic_files(
    directory: str,
    num_files: int,
    language: str = "python",
    min_lines: int = 50,
    max_lines: int = 500,
    complexity: str = "medium",
) -> Tuple[str, int]:
    """
    Create synthetic files for benchmarking.

    Args:
        directory: Directory to create files in
        num_files: Number of files to create
        language: Language to use for files
        min_lines: Minimum number of lines per file
        max_lines: Maximum number of lines per file
        complexity: Complexity level (simple, medium, complex)

    Returns:
        Tuple of (directory, number of files created)
    """
    # Create a temporary directory if not provided
    if not directory:
        directory = tempfile.mkdtemp(prefix="ast_grep_benchmark_")
    else:
        os.makedirs(directory, exist_ok=True)

    analyzer = AstAnalyzer()
    extension = analyzer.supported_languages.get(language, [".py"])[0]

    # Sample Python code templates with increasing complexity
    python_templates = {
        "simple": [
            "def {func_name}({params}):\n    return {value}\n\n",
            "class {class_name}:\n    pass\n\n",
            "x = {value}\n\n",
            "if {condition}:\n    pass\n\n",
            "for i in range({value}):\n    pass\n\n",
        ],
        "medium": [
            "def {func_name}({params}):\n    return {value}\n\n",
            "class {class_name}:\n    def __init__(self):\n        self.value = {value}\n\n",
            "for i in range({value}):\n    print(i)\n\n",
            "if {condition}:\n    print('{message}')\n\n",
            "try:\n    x = {value}\nexcept Exception as e:\n    print(e)\n\n",
        ],
        "complex": [
            'def {func_name}({params}):\n    """Function docstring."""\n    result = 0\n    for i in range({value}):\n        if i % 2 == 0:\n            result += i\n        else:\n            result -= i\n    return result\n\n',
            'class {class_name}:\n    """Class docstring."""\n    def __init__(self, value={value}):\n        self.value = value\n        self.items = []\n    \n    def add_item(self, item):\n        self.items.append(item)\n        return len(self.items)\n\n',
            "def complex_function():\n    result = []\n    for i in range({value}):\n        inner = []\n        for j in range(i):\n            if j % 2 == 0:\n                inner.append(j * 2)\n            else:\n                inner.append(j * 3)\n        result.append(inner)\n    return result\n\n",
        ],
    }

    # Sample JavaScript code templates with increasing complexity
    js_templates = {
        "simple": [
            "function {func_name}({params}) {\n    return {value};\n}\n\n",
            "class {class_name} {}\n\n",
            "let x = {value};\n\n",
            "if ({condition}) {}\n\n",
            "for (let i = 0; i < {value}; i++) {}\n\n",
        ],
        "medium": [
            "function {func_name}({params}) {\n    return {value};\n}\n\n",
            "class {class_name} {\n    constructor() {\n        this.value = {value};\n    }\n}\n\n",
            "for (let i = 0; i < {value}; i++) {\n    console.log(i);\n}\n\n",
            "if ({condition}) {\n    console.log('{message}');\n}\n\n",
            "try {\n    let x = {value};\n} catch (e) {\n    console.error(e);\n}\n\n",
        ],
        "complex": [
            "function {func_name}({params}) {\n    /**\n     * Function documentation\n     */\n    let result = 0;\n    for (let i = 0; i < {value}; i++) {\n        if (i % 2 === 0) {\n            result += i;\n        } else {\n            result -= i;\n        }\n    }\n    return result;\n}\n\n",
            "class {class_name} {\n    /**\n     * Class documentation\n     */\n    constructor(value = {value}) {\n        this.value = value;\n        this.items = [];\n    }\n    \n    addItem(item) {\n        this.items.push(item);\n        return this.items.length;\n    }\n}\n\n",
            "function complexFunction() {\n    const result = [];\n    for (let i = 0; i < {value}; i++) {\n        const inner = [];\n        for (let j = 0; j < i; j++) {\n            if (j % 2 === 0) {\n                inner.push(j * 2);\n            } else {\n                inner.push(j * 3);\n            }\n        }\n        result.push(inner);\n    }\n    return result;\n}\n\n",
        ],
    }

    # Choose templates based on language and complexity
    if language == "python":
        templates = python_templates.get(complexity, python_templates["medium"])
    else:
        templates = js_templates.get(complexity, js_templates["medium"])

    # Create files
    files_created = 0
    for i in range(num_files):
        file_path = Path(directory) / f"synthetic_{i}{extension}"

        # Generate file content
        lines = random.randint(min_lines, max_lines)
        content = ""

        # Each template creates about 5-15 lines depending on complexity
        templates_per_file = max(3, lines // 10)

        for _ in range(templates_per_file):
            template = random.choice(templates)

            # Fill in template with random values
            content += template.format(
                func_name=f"func_{random.randint(1, 1000)}",
                class_name=f"Class_{random.randint(1, 1000)}",
                params=", ".join([f"p{j}" for j in range(random.randint(0, 5))]),
                value=random.randint(1, 100),
                condition=(
                    random.choice(["True", "False"])
                    if language == "python"
                    else random.choice(["true", "false"])
                ),
                message="".join(random.choices(string.ascii_letters, k=10)),
            )

        # Write to file
        with open(file_path, "w") as f:
            f.write(content)

        files_created += 1

    # Create some larger files to test more complex patterns
    if num_files >= 20:
        # Add a few larger files with more complex patterns
        for i in range(min(5, num_files // 20)):
            file_path = Path(directory) / f"synthetic_large_{i}{extension}"
            lines = max_lines * 2
            content = ""

            # Use complex templates
            complex_templates = (
                python_templates["complex"]
                if language == "python"
                else js_templates["complex"]
            )
            for _ in range(lines // 20):
                template = random.choice(complex_templates)
                content += template.format(
                    func_name=f"complex_func_{random.randint(1, 1000)}",
                    class_name=f"ComplexClass_{random.randint(1, 1000)}",
                    params=", ".join(
                        [f"param{j}" for j in range(random.randint(1, 7))]
                    ),
                    value=random.randint(10, 1000),
                    condition=(
                        random.choice(["True", "False"])
                        if language == "python"
                        else random.choice(["true", "false"])
                    ),
                    message="".join(random.choices(string.ascii_letters, k=20)),
                )

            with open(file_path, "w") as f:
                f.write(content)

            files_created += 1

    logger.info(f"Created {files_created} synthetic {language} files in {directory}")
    return directory, files_created


def run_benchmarks(
    output_dir: Optional[str] = None,
    num_files: int = 200,
    batch_sizes: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Run benchmarks to compare performance with and without optimizations.

    Args:
        output_dir: Directory to output benchmark results
        num_files: Number of synthetic files to create for testing
        batch_sizes: List of batch sizes to test (default: [None, 5, 10, 20])

    Returns:
        Dictionary with benchmark results
    """
    from ..ast_analyzer import AstAnalyzer
    from ..utils import result_cache

    # Set default batch sizes if not provided
    if batch_sizes is None:
        batch_sizes = [None, 5, 10, 20]

    benchmark = Benchmark("AST Grep Performance", iterations=3)
    analyzer = AstAnalyzer()

    # Create synthetic files
    temp_dir, created_files = create_synthetic_files(
        output_dir or tempfile.mkdtemp(prefix="ast_grep_benchmark_"),
        num_files,
        language="python",
    )

    # Define search patterns
    patterns = [
        "def $FUNC_NAME($$$PARAMS)",  # Function definition
        "class $CLASS_NAME",  # Class definition
        "for $VAR in $ITERABLE",  # For loop
    ]

    # Test sequential search as baseline
    for pattern in patterns:
        logger.info(f"Testing pattern: {pattern}")

        # Sequential search
        benchmark.run_benchmark(
            f"Sequential search - {pattern}",
            analyzer.search_directory,
            temp_dir,
            pattern,
            parallel=False,
        )

    # Test parallel search with different batch sizes
    for batch_size in batch_sizes:
        batch_label = f"batch_size={batch_size}" if batch_size else "auto_batch"

        for pattern in patterns:
            # Clear cache between runs
            if hasattr(result_cache, "clear"):
                result_cache.clear()

            # Parallel search with current batch size
            benchmark.run_benchmark(
                f"Parallel search ({batch_label}) - {pattern}",
                analyzer.search_directory,
                temp_dir,
                pattern,
                parallel=True,
                batch_size=batch_size,
            )

    # Print results
    benchmark.print_results()

    # Compare results for each pattern and batch size
    comparisons = {}
    best_speedups = {}

    for pattern in patterns:
        pattern_comparisons = {}
        best_speedup = 0
        best_config = None

        for batch_size in batch_sizes:
            batch_label = f"batch_size={batch_size}" if batch_size else "auto_batch"
            parallel_label = f"Parallel search ({batch_label}) - {pattern}"

            comparison = benchmark.compare(
                f"Sequential search - {pattern}", parallel_label
            )

            pattern_comparisons[batch_label] = comparison

            # Track best configuration
            speedup_ratio = comparison.get("speedup_ratio", 0)
            if speedup_ratio > best_speedup:
                best_speedup = speedup_ratio
                best_config = batch_label

        comparisons[pattern] = pattern_comparisons
        best_speedups[pattern] = {"config": best_config, "speedup": best_speedup}

        # Log results for this pattern
        logger.info(f"Pattern: {pattern}")
        logger.info(
            f"  Best configuration: {best_config} with {best_speedup:.2f}x speedup"
        )

        # Log all configurations with their speedups
        for batch_label, comparison in pattern_comparisons.items():
            speedup_ratio = comparison["speedup_ratio"]
            speedup_percentage = comparison["speedup_percentage"]
            logger.info(
                f"  {batch_label}: {speedup_ratio:.2f}x speedup ({speedup_percentage:.2f}%)"
            )

    # Calculate overall best configuration
    avg_speedups = {}
    for batch_size in batch_sizes:
        batch_label = f"batch_size={batch_size}" if batch_size else "auto_batch"
        speedups = []

        for pattern in patterns:
            comparison = comparisons[pattern].get(batch_label)
            if comparison and "speedup_ratio" in comparison:
                speedups.append(comparison["speedup_ratio"])

        if speedups:
            avg_speedups[batch_label] = statistics.mean(speedups)

    best_overall_config = max(avg_speedups.items(), key=lambda x: x[1])
    best_avg_speedup = best_overall_config[1]
    best_config_name = best_overall_config[0]

    success = best_avg_speedup >= 1.2  # 20% or more speedup

    logger.info(
        f"Best overall configuration: {best_config_name} with {best_avg_speedup:.2f}x speedup"
    )
    logger.info(f"Target speedup achieved: {success}")

    # Prepare detailed results
    detailed_results = {
        "success": success,
        "best_config": best_config_name,
        "best_avg_speedup": best_avg_speedup,
        "best_avg_speedup_percentage": (best_avg_speedup - 1) * 100,
        "pattern_results": {},
        "num_files": created_files,
        "temp_dir": temp_dir,
    }

    # Add per-pattern results
    for pattern in patterns:
        pattern_stats = best_speedups[pattern]

        detailed_results["pattern_results"][pattern] = {
            "best_config": pattern_stats["config"],
            "best_speedup": pattern_stats["speedup"],
            "best_speedup_percentage": (pattern_stats["speedup"] - 1) * 100,
        }

    return detailed_results
