---
description: Check sandbox system status and health
---

Check the health and status of the sandbox system.

Run comprehensive status checks:

```bash
cd "D:\GAO Agile Dev"

echo "=== Sandbox Projects ==="
python -m gao_dev.cli.commands sandbox list

echo ""
echo "=== Available Benchmarks ==="
ls -1 sandbox/benchmarks/*.yaml 2>/dev/null | wc -l

echo ""
echo "=== Recent Reports ==="
ls -lh sandbox/reports/*.html 2>/dev/null | head -5 || echo "No reports found"

echo ""
echo "=== Disk Usage ==="
du -sh sandbox/projects/* 2>/dev/null | tail -5 || echo "No projects found"

echo ""
echo "=== Git Check ==="
git --version

echo ""
echo "=== Python Environment ==="
python --version
pip show gao-dev | grep Version || echo "gao-dev not installed"
```

After running checks, provide a summary:
1. Number of active projects
2. Number of available benchmarks
3. Total disk space used
4. System health status (all dependencies available?)
5. Recommendations for cleanup if needed
