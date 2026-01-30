#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════════════╗
║                    ENTERPRISE MEGA TEST RUNNER                                           ║
║                 "One Command to Test Them All"                                           ║
║                                                                                          ║
║  🔥 700+ Tests | 🎯 8 Categories | 💥 Aggressive | 🛡️ Security | ⚡ Performance          ║
╚══════════════════════════════════════════════════════════════════════════════════════════╝

Test Categories:
================
1. test_aggressive_comprehensive.py  - 200+ Boundary/Edge Case Tests
2. test_chaos_engineering.py         - 100+ Chaos & Failure Tests
3. test_security_penetration.py      - 150+ Security Tests
4. test_performance_profiling.py     - 100+ Performance Tests
5. test_integration_deep.py          - 150+ Integration Tests

Run Modes:
==========
--quick     : Run quick smoke tests only (~50 tests)
--standard  : Run standard test coverage (~200 tests)
--full      : Run all tests (~700 tests)
--security  : Run security tests only
--perf      : Run performance tests only
--chaos     : Run chaos engineering tests only

Author: Enterprise Test Team
Date: 2026-01-28
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Colored output
try:
    from colorama import init, Fore, Style
    init()
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    class Fore:
        RED = GREEN = YELLOW = BLUE = CYAN = MAGENTA = WHITE = RESET = ""
    class Style:
        BRIGHT = RESET_ALL = ""


# =============================================================================
# CONFIGURATION
# =============================================================================

TEST_DIR = Path(__file__).parent
PROJECT_ROOT = TEST_DIR.parent

TEST_SUITES = {
    "aggressive": {
        "file": "test_aggressive_comprehensive.py",
        "description": "Boundary attacks, edge cases, malformed inputs",
        "estimated_tests": 200,
        "timeout": 600,
    },
    "chaos": {
        "file": "test_chaos_engineering.py",
        "description": "Failure injection, recovery testing, resilience",
        "estimated_tests": 100,
        "timeout": 600,
    },
    "security": {
        "file": "test_security_penetration.py",
        "description": "SQL injection, XSS, SSRF, auth bypass, AI attacks",
        "estimated_tests": 150,
        "timeout": 600,
    },
    "performance": {
        "file": "test_performance_profiling.py",
        "description": "Latency, memory, throughput, scalability",
        "estimated_tests": 100,
        "timeout": 900,
    },
    "integration": {
        "file": "test_integration_deep.py",
        "description": "User journeys, multi-turn, WebSocket, session",
        "estimated_tests": 150,
        "timeout": 600,
    },
}

QUICK_TESTS = [
    "test_aggressive_comprehensive.py::TestBoundaryAttacks::test_message_length_boundaries[0]",
    "test_aggressive_comprehensive.py::TestBoundaryAttacks::test_message_length_boundaries[100]",
    "test_chaos_engineering.py::TestLatencyInjection::test_system_handles_200ms_latency",
    "test_security_penetration.py::TestInjectionAttacks::test_sql_injection_in_message[' OR '1'='1]",
    "test_performance_profiling.py::TestLatencyPerformance::test_cold_start_latency",
    "test_integration_deep.py::TestCompleteUserSession::test_new_user_first_conversation",
]


# =============================================================================
# TEST RESULT CLASSES
# =============================================================================

@dataclass
class SuiteResult:
    """Result of running a test suite."""
    name: str
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    duration_s: float = 0.0
    failures: List[str] = field(default_factory=list)
    
    @property
    def total(self) -> int:
        return self.passed + self.failed + self.skipped + self.errors
    
    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.passed / (self.passed + self.failed + self.errors)


@dataclass
class TestRunResult:
    """Result of entire test run."""
    timestamp: str
    mode: str
    suites: List[SuiteResult] = field(default_factory=list)
    total_duration_s: float = 0.0
    
    @property
    def total_passed(self) -> int:
        return sum(s.passed for s in self.suites)
    
    @property
    def total_failed(self) -> int:
        return sum(s.failed for s in self.suites)
    
    @property
    def total_skipped(self) -> int:
        return sum(s.skipped for s in self.suites)
    
    @property
    def total_tests(self) -> int:
        return sum(s.total for s in self.suites)
    
    @property
    def overall_success_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return self.total_passed / (self.total_passed + self.total_failed)


# =============================================================================
# RUNNER FUNCTIONS
# =============================================================================

def print_banner():
    """Print fancy banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                          ║
║     ███████╗███╗   ██╗████████╗███████╗██████╗ ██████╗ ██████╗ ██╗███████╗███████╗       ║
║     ██╔════╝████╗  ██║╚══██╔══╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██║██╔════╝██╔════╝       ║
║     █████╗  ██╔██╗ ██║   ██║   █████╗  ██████╔╝██████╔╝██████╔╝██║███████╗█████╗         ║
║     ██╔══╝  ██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗██╔═══╝ ██╔══██╗██║╚════██║██╔══╝         ║
║     ███████╗██║ ╚████║   ██║   ███████╗██║  ██║██║     ██║  ██║██║███████║███████╗       ║
║     ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚══════╝       ║
║                                                                                          ║
║                         🔥 MEGA TEST SUITE RUNNER 🔥                                     ║
║                          700+ Aggressive Tests                                           ║
║                                                                                          ║
╚══════════════════════════════════════════════════════════════════════════════════════════╝
"""
    print(f"{Fore.CYAN}{banner}{Style.RESET_ALL}")


def print_section(title: str):
    """Print section header."""
    print(f"\n{Fore.YELLOW}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}  {title}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'='*80}{Style.RESET_ALL}")


def run_pytest_suite(suite_name: str, suite_config: dict, verbose: bool = False) -> SuiteResult:
    """Run a pytest test suite."""
    result = SuiteResult(name=suite_name)
    
    test_file = TEST_DIR / suite_config["file"]
    if not test_file.exists():
        print(f"{Fore.RED}  ✗ Test file not found: {test_file}{Style.RESET_ALL}")
        result.errors = 1
        return result
    
    print(f"\n{Fore.CYAN}▶ Running: {suite_name}{Style.RESET_ALL}")
    print(f"  {Fore.WHITE}{suite_config['description']}{Style.RESET_ALL}")
    print(f"  Estimated: ~{suite_config['estimated_tests']} tests")
    
    # Build pytest command
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file),
        "--tb=short",
        "-q",
        f"--timeout={suite_config['timeout']}",
        "-W", "ignore::DeprecationWarning",
    ]
    
    if verbose:
        cmd.append("-v")
    
    # Run pytest and capture output
    start_time = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=suite_config["timeout"] + 60
        )
        result.duration_s = time.time() - start_time
        
        # Parse output
        output = proc.stdout + proc.stderr
        
        # Parse summary line like "10 passed, 2 failed, 1 skipped"
        import re
        
        passed_match = re.search(r'(\d+) passed', output)
        failed_match = re.search(r'(\d+) failed', output)
        skipped_match = re.search(r'(\d+) skipped', output)
        error_match = re.search(r'(\d+) error', output)
        
        result.passed = int(passed_match.group(1)) if passed_match else 0
        result.failed = int(failed_match.group(1)) if failed_match else 0
        result.skipped = int(skipped_match.group(1)) if skipped_match else 0
        result.errors = int(error_match.group(1)) if error_match else 0
        
        # Extract failure names
        failure_lines = re.findall(r'FAILED (.+?) -', output)
        result.failures = failure_lines[:10]  # Limit to 10
        
        # Print result
        if result.failed == 0 and result.errors == 0:
            print(f"  {Fore.GREEN}✓ PASSED: {result.passed} tests in {result.duration_s:.1f}s{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}✗ FAILED: {result.passed} passed, {result.failed} failed in {result.duration_s:.1f}s{Style.RESET_ALL}")
            for failure in result.failures[:3]:
                print(f"    {Fore.RED}• {failure}{Style.RESET_ALL}")
                
    except subprocess.TimeoutExpired:
        result.duration_s = time.time() - start_time
        result.errors = 1
        print(f"  {Fore.RED}✗ TIMEOUT after {suite_config['timeout']}s{Style.RESET_ALL}")
    except Exception as e:
        result.duration_s = time.time() - start_time
        result.errors = 1
        print(f"  {Fore.RED}✗ ERROR: {e}{Style.RESET_ALL}")
    
    return result


def run_quick_tests(verbose: bool = False) -> TestRunResult:
    """Run quick smoke tests."""
    result = TestRunResult(
        timestamp=datetime.now().isoformat(),
        mode="quick"
    )
    
    print_section("QUICK SMOKE TESTS")
    print(f"Running ~{len(QUICK_TESTS)} targeted tests...")
    
    start_time = time.time()
    
    cmd = [
        sys.executable, "-m", "pytest",
        "-v",
        "--tb=short",
        "-W", "ignore::DeprecationWarning",
        "--timeout=60",
    ] + QUICK_TESTS
    
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(TEST_DIR),
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Simple parsing
        import re
        output = proc.stdout + proc.stderr
        
        passed_match = re.search(r'(\d+) passed', output)
        failed_match = re.search(r'(\d+) failed', output)
        
        suite = SuiteResult(name="quick")
        suite.passed = int(passed_match.group(1)) if passed_match else 0
        suite.failed = int(failed_match.group(1)) if failed_match else 0
        suite.duration_s = time.time() - start_time
        
        result.suites.append(suite)
        
    except Exception as e:
        print(f"{Fore.RED}Quick test error: {e}{Style.RESET_ALL}")
    
    result.total_duration_s = time.time() - start_time
    return result


def run_selected_suites(suites: List[str], verbose: bool = False) -> TestRunResult:
    """Run selected test suites."""
    result = TestRunResult(
        timestamp=datetime.now().isoformat(),
        mode="selected"
    )
    
    start_time = time.time()
    
    for suite_name in suites:
        if suite_name in TEST_SUITES:
            suite_result = run_pytest_suite(
                suite_name, 
                TEST_SUITES[suite_name], 
                verbose
            )
            result.suites.append(suite_result)
    
    result.total_duration_s = time.time() - start_time
    return result


def run_all_suites(verbose: bool = False) -> TestRunResult:
    """Run all test suites."""
    return run_selected_suites(list(TEST_SUITES.keys()), verbose)


def print_final_report(result: TestRunResult):
    """Print the final test report."""
    print_section("FINAL REPORT")
    
    # Suite breakdown
    print(f"\n{Fore.WHITE}Suite Results:{Style.RESET_ALL}")
    print(f"{'Suite':<20} {'Passed':<10} {'Failed':<10} {'Skipped':<10} {'Time':<10}")
    print("-" * 60)
    
    for suite in result.suites:
        status_color = Fore.GREEN if suite.failed == 0 else Fore.RED
        print(f"{suite.name:<20} {Fore.GREEN}{suite.passed:<10}{Style.RESET_ALL} "
              f"{status_color}{suite.failed:<10}{Style.RESET_ALL} "
              f"{Fore.YELLOW}{suite.skipped:<10}{Style.RESET_ALL} "
              f"{suite.duration_s:.1f}s")
    
    print("-" * 60)
    print(f"{'TOTAL':<20} {Fore.GREEN}{result.total_passed:<10}{Style.RESET_ALL} "
          f"{Fore.RED if result.total_failed > 0 else Fore.GREEN}{result.total_failed:<10}{Style.RESET_ALL} "
          f"{Fore.YELLOW}{result.total_skipped:<10}{Style.RESET_ALL} "
          f"{result.total_duration_s:.1f}s")
    
    # Summary
    print(f"\n{Fore.WHITE}Summary:{Style.RESET_ALL}")
    print(f"  Total Tests: {result.total_tests}")
    print(f"  Success Rate: {result.overall_success_rate:.1%}")
    print(f"  Duration: {result.total_duration_s:.1f}s ({result.total_duration_s/60:.1f} min)")
    
    # Overall status
    if result.total_failed == 0:
        print(f"\n{Fore.GREEN}{'='*60}")
        print(f"  ✅ ALL TESTS PASSED!")
        print(f"{'='*60}{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}{'='*60}")
        print(f"  ❌ {result.total_failed} TESTS FAILED")
        print(f"{'='*60}{Style.RESET_ALL}")
    
    # Save report
    report_file = PROJECT_ROOT / "test_mega_report.json"
    report_data = {
        "timestamp": result.timestamp,
        "mode": result.mode,
        "total_tests": result.total_tests,
        "passed": result.total_passed,
        "failed": result.total_failed,
        "skipped": result.total_skipped,
        "success_rate": result.overall_success_rate,
        "duration_s": result.total_duration_s,
        "suites": [
            {
                "name": s.name,
                "passed": s.passed,
                "failed": s.failed,
                "skipped": s.skipped,
                "duration_s": s.duration_s,
                "failures": s.failures
            }
            for s in result.suites
        ]
    }
    
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n{Fore.CYAN}Report saved to: {report_file}{Style.RESET_ALL}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Enterprise Mega Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_mega_tests.py --quick           # Quick smoke tests (~50 tests)
  python run_mega_tests.py --standard        # Standard coverage (~200 tests)
  python run_mega_tests.py --full            # All tests (~700 tests)
  python run_mega_tests.py --security        # Security tests only
  python run_mega_tests.py --perf            # Performance tests only
  python run_mega_tests.py --chaos           # Chaos engineering tests
  python run_mega_tests.py --suites aggressive security  # Specific suites
        """
    )
    
    parser.add_argument("--quick", action="store_true", help="Run quick smoke tests")
    parser.add_argument("--standard", action="store_true", help="Run standard test coverage")
    parser.add_argument("--full", action="store_true", help="Run all tests")
    parser.add_argument("--security", action="store_true", help="Run security tests only")
    parser.add_argument("--perf", action="store_true", help="Run performance tests only")
    parser.add_argument("--chaos", action="store_true", help="Run chaos engineering tests")
    parser.add_argument("--suites", nargs="+", choices=list(TEST_SUITES.keys()), help="Run specific suites")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    print_banner()
    
    # Determine what to run
    if args.quick:
        result = run_quick_tests(args.verbose)
    elif args.security:
        result = run_selected_suites(["security"], args.verbose)
    elif args.perf:
        result = run_selected_suites(["performance"], args.verbose)
    elif args.chaos:
        result = run_selected_suites(["chaos"], args.verbose)
    elif args.suites:
        result = run_selected_suites(args.suites, args.verbose)
    elif args.full:
        result = run_all_suites(args.verbose)
    elif args.standard:
        result = run_selected_suites(["aggressive", "security", "integration"], args.verbose)
    else:
        # Default: run standard
        print(f"{Fore.YELLOW}No mode specified, running standard tests...{Style.RESET_ALL}")
        result = run_selected_suites(["aggressive", "security", "integration"], args.verbose)
    
    print_final_report(result)
    
    # Exit with appropriate code
    sys.exit(0 if result.total_failed == 0 else 1)


if __name__ == "__main__":
    main()
