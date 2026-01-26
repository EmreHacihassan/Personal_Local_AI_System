"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║           PREMIUM TEST ORCHESTRATOR - COMPREHENSIVE TEST RUNNER               ║
║                                                                                 ║
║  Features:                                                                      ║
║  - Runs all 15 test phases                                                      ║
║  - Generates detailed JSON and HTML reports                                     ║
║  - Provides self-healing suggestions                                            ║
║  - Tracks historical test results                                               ║
║  - Adaptive introspection for robust testing                                    ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import importlib.util

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.critical_protocol.base_premium_test import (
    AdaptiveIntrospector,
    SelfHealingTestRunner,
    TestDiscovery,
    TestStatus
)


class PremiumTestOrchestrator:
    """
    Premium test orchestrator that runs all phases and generates reports
    """
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.protocol_dir = Path(__file__).parent
        self.introspector = AdaptiveIntrospector(self.project_root)
        self.discovery = TestDiscovery(self.project_root)
        self.results: Dict[int, Dict[str, Any]] = {}
        self.start_time: datetime = None
        self.end_time: datetime = None
        
    def discover_phase_tests(self) -> Dict[int, Path]:
        """Discover all phase test files"""
        phases = {}
        
        for f in self.protocol_dir.glob("phase_*.py"):
            # Extract phase number
            name = f.stem
            try:
                phase_num = int(name.split("_")[1])
                phases[phase_num] = f
            except (IndexError, ValueError):
                continue
                
        return dict(sorted(phases.items()))
        
    async def run_phase(self, phase_num: int, phase_file: Path) -> Dict[str, Any]:
        """Run a single phase test"""
        print(f"\n{'='*70}")
        print(f"  Running Phase {phase_num}: {phase_file.stem}")
        print(f"{'='*70}")
        
        try:
            # Load the module dynamically
            spec = importlib.util.spec_from_file_location(
                f"phase_{phase_num:02d}",
                phase_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find and run the main function
            if hasattr(module, 'main'):
                result = await module.main()
                return result
            else:
                # Try to find the Phase class
                for name in dir(module):
                    obj = getattr(module, name)
                    if isinstance(obj, type) and name.startswith("Phase"):
                        instance = obj()
                        if hasattr(instance, 'run_all_tests'):
                            result = await instance.run_all_tests()
                            return result
                            
                return {
                    "phase": f"Phase {phase_num}",
                    "error": "No runnable test found",
                    "passed": 0,
                    "failed": 1,
                    "total": 1,
                    "success_rate": 0
                }
                
        except Exception as e:
            import traceback
            return {
                "phase": f"Phase {phase_num}",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "passed": 0,
                "failed": 1,
                "total": 1,
                "success_rate": 0
            }
            
    async def run_all_phases(self, 
                            phases_to_run: List[int] = None,
                            parallel: bool = False) -> Dict[str, Any]:
        """Run all phases (or specified phases)"""
        self.start_time = datetime.now()
        
        print("\n" + "╔" + "═"*68 + "╗")
        print("║" + " "*20 + "PREMIUM TEST ORCHESTRATOR" + " "*23 + "║")
        print("║" + " "*15 + f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}" + " "*19 + "║")
        print("╚" + "═"*68 + "╝")
        
        phases = self.discover_phase_tests()
        
        if phases_to_run:
            phases = {k: v for k, v in phases.items() if k in phases_to_run}
            
        if parallel:
            # Run all phases in parallel
            tasks = [
                self.run_phase(num, path) 
                for num, path in phases.items()
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, (num, _) in enumerate(phases.items()):
                if isinstance(results[i], Exception):
                    self.results[num] = {
                        "phase": f"Phase {num}",
                        "error": str(results[i]),
                        "passed": 0,
                        "failed": 1,
                        "total": 1,
                        "success_rate": 0
                    }
                else:
                    self.results[num] = results[i]
        else:
            # Run sequentially
            for num, path in phases.items():
                self.results[num] = await self.run_phase(num, path)
                
        self.end_time = datetime.now()
        return self.generate_summary()
        
    def generate_summary(self) -> Dict[str, Any]:
        """Generate comprehensive summary"""
        total_tests = 0
        total_passed = 0
        total_failed = 0
        
        phase_summaries = []
        
        for num, result in sorted(self.results.items()):
            phase_total = result.get('total', 1)
            phase_passed = result.get('passed', 0)
            phase_failed = result.get('failed', 1)
            
            total_tests += phase_total
            total_passed += phase_passed
            total_failed += phase_failed
            
            phase_summaries.append({
                "phase_number": num,
                "phase_name": result.get('phase', f'Phase {num}'),
                "total": phase_total,
                "passed": phase_passed,
                "failed": phase_failed,
                "success_rate": result.get('success_rate', 0),
                "status": "✓ PERFECT" if phase_failed == 0 else "✗ NEEDS FIX"
            })
            
        duration = (self.end_time - self.start_time).total_seconds()
        overall_rate = (100 * total_passed / total_tests) if total_tests > 0 else 0
        
        # Determine verdict
        if overall_rate == 100:
            verdict = "PERFECT - PREMIUM GRADE"
        elif overall_rate >= 95:
            verdict = "EXCELLENT"
        elif overall_rate >= 90:
            verdict = "VERY GOOD"
        elif overall_rate >= 80:
            verdict = "GOOD"
        else:
            verdict = "NEEDS IMPROVEMENT"
            
        summary = {
            "timestamp": self.start_time.isoformat(),
            "duration_seconds": round(duration, 2),
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "success_rate": round(overall_rate, 2),
            "verdict": verdict,
            "phases": phase_summaries
        }
        
        # Print summary
        print("\n" + "╔" + "═"*68 + "╗")
        print("║" + " "*22 + "FINAL SUMMARY" + " "*33 + "║")
        print("╠" + "═"*68 + "╣")
        
        for ps in phase_summaries:
            status = "✓" if ps['failed'] == 0 else "✗"
            line = f"  {status} Phase {ps['phase_number']:02d}: {ps['passed']}/{ps['total']} ({ps['success_rate']:.1f}%)"
            print(f"║{line:<68}║")
            
        print("╠" + "═"*68 + "╣")
        print(f"║  Total Tests: {total_tests:<54}║")
        print(f"║  Passed: {total_passed:<59}║")
        print(f"║  Failed: {total_failed:<59}║")
        print(f"║  Success Rate: {overall_rate:.2f}%{' '*(52-len(f'{overall_rate:.2f}'))}║")
        print(f"║  Duration: {duration:.2f}s{' '*(54-len(f'{duration:.2f}'))}║")
        print(f"║  Verdict: {verdict:<57}║")
        print("╚" + "═"*68 + "╝")
        
        return summary
        
    def save_report(self, summary: Dict[str, Any], 
                   json_path: Path = None,
                   html_path: Path = None):
        """Save reports to files"""
        if json_path is None:
            json_path = self.protocol_dir / "test_report.json"
            
        # Save JSON report
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"\n📄 JSON report saved: {json_path}")
        
        # Save HTML report
        if html_path is None:
            html_path = self.protocol_dir / "test_report.html"
            
        html_content = self._generate_html_report(summary)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"📄 HTML report saved: {html_path}")
        
    def _generate_html_report(self, summary: Dict[str, Any]) -> str:
        """Generate HTML report"""
        phases_html = ""
        for ps in summary['phases']:
            status_class = "passed" if ps['failed'] == 0 else "failed"
            phases_html += f"""
            <tr class="{status_class}">
                <td>Phase {ps['phase_number']:02d}</td>
                <td>{ps['phase_name']}</td>
                <td>{ps['passed']}</td>
                <td>{ps['failed']}</td>
                <td>{ps['total']}</td>
                <td>{ps['success_rate']:.1f}%</td>
                <td>{ps['status']}</td>
            </tr>
            """
            
        verdict_class = "perfect" if summary['success_rate'] == 100 else "warning"
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Premium Test Report - AgenticManagingSystem</title>
    <style>
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 28px;
        }}
        .header .timestamp {{
            opacity: 0.9;
            font-size: 14px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .summary-card .value {{
            font-size: 36px;
            font-weight: bold;
            color: #333;
        }}
        .summary-card .label {{
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }}
        .summary-card.perfect .value {{ color: #22c55e; }}
        .summary-card.warning .value {{ color: #eab308; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
        }}
        tr.passed {{ background: #f0fdf4; }}
        tr.failed {{ background: #fef2f2; }}
        .status {{ font-weight: bold; }}
        tr.passed .status {{ color: #22c55e; }}
        tr.failed .status {{ color: #ef4444; }}
        .verdict {{
            font-size: 24px;
            font-weight: bold;
            text-align: center;
            padding: 20px;
            margin-top: 30px;
            border-radius: 8px;
        }}
        .verdict.perfect {{
            background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
            color: white;
        }}
        .verdict.warning {{
            background: linear-gradient(135deg, #eab308 0%, #ca8a04 100%);
            color: white;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏆 Premium Test Protocol Report</h1>
        <div class="timestamp">Generated: {summary['timestamp']}</div>
    </div>
    
    <div class="summary">
        <div class="summary-card">
            <div class="value">{summary['total_tests']}</div>
            <div class="label">Total Tests</div>
        </div>
        <div class="summary-card">
            <div class="value" style="color: #22c55e;">{summary['total_passed']}</div>
            <div class="label">Passed</div>
        </div>
        <div class="summary-card">
            <div class="value" style="color: #ef4444;">{summary['total_failed']}</div>
            <div class="label">Failed</div>
        </div>
        <div class="summary-card {verdict_class}">
            <div class="value">{summary['success_rate']}%</div>
            <div class="label">Success Rate</div>
        </div>
        <div class="summary-card">
            <div class="value">{summary['duration_seconds']}s</div>
            <div class="label">Duration</div>
        </div>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>Phase</th>
                <th>Name</th>
                <th>Passed</th>
                <th>Failed</th>
                <th>Total</th>
                <th>Rate</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {phases_html}
        </tbody>
    </table>
    
    <div class="verdict {verdict_class}">
        {summary['verdict']}
    </div>
</body>
</html>
        """


class IncrementalValidator:
    """
    Validates module compatibility and suggests fixes
    """
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.introspector = AdaptiveIntrospector(self.project_root)
        
    def validate_module(self, module_path: str) -> Dict[str, Any]:
        """Validate a module and return detailed report"""
        info = self.introspector.discover_module(module_path)
        
        return {
            "module": module_path,
            "can_import": info.can_import,
            "path": info.path,
            "classes": info.classes,
            "functions": info.functions,
            "constants_count": len(info.constants),
            "error": info.error
        }
        
    def validate_all_core_modules(self) -> List[Dict[str, Any]]:
        """Validate all core modules"""
        results = []
        core_dir = self.project_root / "core"
        
        for py_file in sorted(core_dir.glob("*.py")):
            if py_file.name.startswith('_'):
                continue
                
            module_path = f"core.{py_file.stem}"
            results.append(self.validate_module(module_path))
            
        return results
        
    def generate_compatibility_report(self) -> str:
        """Generate a compatibility report for all modules"""
        results = self.validate_all_core_modules()
        
        report = ["# Core Module Compatibility Report\n"]
        report.append(f"Generated: {datetime.now().isoformat()}\n\n")
        
        importable = sum(1 for r in results if r['can_import'])
        report.append(f"**Summary**: {importable}/{len(results)} modules importable\n\n")
        
        report.append("## Modules\n\n")
        
        for r in results:
            status = "✓" if r['can_import'] else "✗"
            report.append(f"### {status} {r['module']}\n")
            
            if r['can_import']:
                report.append(f"- Classes: {', '.join(r['classes'][:5])}\n")
                report.append(f"- Functions: {', '.join(r['functions'][:5])}\n")
                report.append(f"- Constants: {r['constants_count']}\n")
            else:
                report.append(f"- Error: {r['error']}\n")
                
            report.append("\n")
            
        return "".join(report)


async def main():
    """Main entry point"""
    orchestrator = PremiumTestOrchestrator()
    
    # Run all phases
    summary = await orchestrator.run_all_phases()
    
    # Save reports
    orchestrator.save_report(summary)
    
    return summary


if __name__ == "__main__":
    asyncio.run(main())
