#!/usr/bin/env python
"""
Quick start guide for the Visualization Benchmark.
This script shows you how to run the benchmark with various configurations.
"""

import subprocess
import sys
from pathlib import Path


def run_benchmark_basic():
    """Run benchmark with default settings."""
    print("=" * 70)
    print("RUNNING BASIC BENCHMARK (All 20 scenarios)")
    print("=" * 70)
    cmd = [sys.executable, "benchmark_visualization.py"]
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode == 0


def run_benchmark_quick():
    """Run quick benchmark (first 5 scenarios)."""
    print("=" * 70)
    print("RUNNING QUICK BENCHMARK (First 5 scenarios)")
    print("=" * 70)
    cmd = [
        sys.executable,
        "benchmark_visualization.py",
        "--limit", "5",
        "--output", "visualization_benchmark_quick.xlsx",
    ]
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode == 0


def run_benchmark_simple():
    """Run simple scenarios only."""
    print("=" * 70)
    print("RUNNING SIMPLE SCENARIOS ONLY")
    print("=" * 70)
    # This would require parsing the scenarios, so we'll use limit
    cmd = [
        sys.executable,
        "benchmark_visualization.py",
        "--limit", "3",
        "--output", "visualization_benchmark_simple.xlsx",
    ]
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode == 0


def run_benchmark_intermediate():
    """Run intermediate to complex scenarios."""
    print("=" * 70)
    print("RUNNING INTERMEDIATE & COMPLEX SCENARIOS")
    print("=" * 70)
    cmd = [
        sys.executable,
        "benchmark_visualization.py",
        "--start", "3",
        "--output", "visualization_benchmark_advanced.xlsx",
    ]
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode == 0


def print_menu():
    """Display the menu of options."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  VISUALIZATION AGENT BENCHMARK - QUICK START".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    print("\nSelect a benchmark option:\n")
    print("  1. Run BASIC benchmark (all 20 scenarios) - ~10-15 minutes")
    print("  2. Run QUICK benchmark (first 5 scenarios) - ~2-3 minutes")
    print("  3. Run SIMPLE scenarios only (3 scenarios) - ~1 minute")
    print("  4. Run INTERMEDIATE & COMPLEX scenarios - ~9-12 minutes")
    print("  5. Custom command (enter manually)")
    print("  0. Exit")
    print("\n" + "=" * 70 + "\n")


def main():
    """Main menu loop."""
    print("\n" + "╔" + "=" * 68 + "╗")
    print("║" + " VISUALIZATION AGENT BENCHMARK ".center(68) + "║")
    print("║" + "─" * 68 + "║")
    print("║" + "This tool benchmarks the Visualization Agent's ability to:".ljust(68) + "║")
    print("║" + "  • Generate visualization code from natural language".ljust(68) + "║")
    print("║" + "  • Execute code safely in a sandbox".ljust(68) + "║")
    print("║" + "  • Handle 20 test scenarios (simple to complex)".ljust(68) + "║")
    print("║" + "  • Measure success rate and quality metrics".ljust(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")

    while True:
        print_menu()
        choice = input("Enter your choice (0-5): ").strip()

        if choice == "0":
            print("Exiting. Goodbye!")
            break
        elif choice == "1":
            if run_benchmark_basic():
                print("\n✓ Benchmark completed!")
            else:
                print("\n✗ Benchmark failed!")
        elif choice == "2":
            if run_benchmark_quick():
                print("\n✓ Quick benchmark completed!")
            else:
                print("\n✗ Quick benchmark failed!")
        elif choice == "3":
            if run_benchmark_simple():
                print("\n✓ Simple benchmark completed!")
            else:
                print("\n✗ Simple benchmark failed!")
        elif choice == "4":
            if run_benchmark_intermediate():
                print("\n✓ Advanced benchmark completed!")
            else:
                print("\n✗ Advanced benchmark failed!")
        elif choice == "5":
            cmd = input("Enter Python command: ").strip()
            if cmd:
                print(f"\nRunning: {cmd}\n")
                result = subprocess.run(cmd, shell=True, cwd=Path(__file__).parent)
                if result.returncode == 0:
                    print("\n✓ Command executed successfully!")
                else:
                    print(f"\n✗ Command failed with exit code {result.returncode}")
        else:
            print("Invalid choice. Please try again.")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    # If run with arguments, execute directly
    if len(sys.argv) > 1:
        if sys.argv[1] == "basic":
            sys.exit(0 if run_benchmark_basic() else 1)
        elif sys.argv[1] == "quick":
            sys.exit(0 if run_benchmark_quick() else 1)
        elif sys.argv[1] == "simple":
            sys.exit(0 if run_benchmark_simple() else 1)
        elif sys.argv[1] == "advanced":
            sys.exit(0 if run_benchmark_intermediate() else 1)
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Usage: python run_benchmark.py [basic|quick|simple|advanced]")
            sys.exit(1)
    else:
        # Otherwise show interactive menu
        main()
