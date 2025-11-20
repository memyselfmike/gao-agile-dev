# GAO-Dev Quick Start Guide

**Choose your path:**

---

## 🎯 Beta Tester (Using GAO-Dev)

**Install:**
```bash
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main
```

**Start:**
```bash
mkdir my-project
cd my-project
gao-dev start  # Launches onboarding + web interface
```

**Upgrade:**
```bash
pip install --upgrade --force-reinstall git+https://github.com/memyselfmike/gao-agile-dev.git@main
```

**Full Guide:** [BETA_TESTING_CHECKLIST.md](BETA_TESTING_CHECKLIST.md)

---

## 🔧 Developer (Contributing to GAO-Dev)

**Install:**
```bash
git clone https://github.com/memyselfmike/gao-agile-dev.git
cd gao-agile-dev
pip install -e ".[dev]"
python verify_install.py  # MUST show all [PASS]
```

**Verify:**
```bash
python verify_install.py  # Check installation health
```

**Develop:**
```bash
# 1. Edit source files
vim gao_dev/cli/chat_repl.py

# 2. Test immediately (no reinstall!)
gao-dev start

# 3. Run tests
pytest
```

**Full Guide:** [CONTRIBUTING.md](CONTRIBUTING.md)

---

## ⚠️ Critical: Don't Mix Modes!

**Never run both:**
```bash
pip install git+https://...  # Beta mode
pip install -e .             # Dev mode
```

**If you mixed them:**
```bash
# Windows
reinstall_dev.bat

# macOS/Linux
./reinstall_dev.sh
```

---

## 🔍 Troubleshooting

| Problem | Solution |
|---------|----------|
| Changes don't take effect | `python verify_install.py` → `reinstall_dev.bat` |
| Import errors | `pip install -e ".[dev]"` |
| Wrong project_root | Run `reinstall_dev.bat` |
| Can't delete files | Close all terminals → run `reinstall_dev.bat` |

**Full Guide:** [DEV_TROUBLESHOOTING.md](DEV_TROUBLESHOOTING.md)

---

## 📚 Documentation

- **[INSTALLATION.md](INSTALLATION.md)** - Complete installation guide
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development guidelines
- **[CLAUDE.md](CLAUDE.md)** - Claude AI agent instructions
- **[BETA_TESTING_CHECKLIST.md](BETA_TESTING_CHECKLIST.md)** - Beta testing guide
- **[DEV_TROUBLESHOOTING.md](DEV_TROUBLESHOOTING.md)** - Detailed troubleshooting

---

## 🆘 Getting Help

- **Issues**: https://github.com/memyselfmike/gao-agile-dev/issues
- **Discussions**: https://github.com/memyselfmike/gao-agile-dev/discussions
- **Documentation**: All *.md files in project root

---

**Last Updated**: 2025-11-20
