# docs/ Root Folder Cleanup Plan

**Date**: 2025-11-06
**Issue**: 23+ files still in docs/ root, many are feature-specific and should be organized

---

## Current State

**Files in docs/ root**: 23 markdown files
**Should have**: ~8-10 core standards/guides only

---

## Categorization & Actions

### ✅ KEEP (8 Core Standards/Guides)

These belong in docs/ root as core project documentation:

1. **BENCHMARK_STANDARDS.md** - Core benchmarking standards
2. **BMAD_METHODOLOGY.md** - BMAD methodology reference
3. **bmm-workflow-status.md** - Current workflow status
4. **INDEX.md** - Master navigation hub (NEW)
5. **plugin-development-guide.md** - Plugin development guide
6. **QA_STANDARDS.md** - QA standards
7. **QUICK_REFERENCE.md** - Quick reference card (NEW)
8. **SETUP.md** - Setup guide

---

### 📦 MOVE to features/agent-provider-abstraction/ (8 files)

Epic 11 (Agent Provider Abstraction) specific documentation:

1. **MIGRATION_PROVIDER.md** → Migration guide for providers
2. **provider-abstraction-analysis.md** → Analysis document
3. **PROVIDER_SYSTEM_GUIDE.md** → System guide
4. **provider-plugin-development.md** → Plugin development
5. **opencode-cli-reference.md** → OpenCode CLI reference
6. **opencode-research.md** → OpenCode research notes
7. **opencode-setup-guide.md** → OpenCode setup
8. **opencode-tool-mapping.md** → Tool mapping

**Reason**: All Epic 11 related, should be with feature docs

---

### 📦 MOVE to features/prompt-abstraction/ (1 file)

Epic 10 (Prompt Abstraction) specific:

1. **MIGRATION_GUIDE_EPIC_10.md** → Migration guide for Epic 10

**Reason**: Epic 10 migration guide belongs with Epic 10 feature docs

---

### 📦 MOVE to features/document-lifecycle-system/ (2 files)

Epic 13 (Document Lifecycle) specific:

1. **MIGRATION_GUIDE_EPIC_13.md** → Migration guide for Epic 13
2. **checklist-authoring-guide.md** → Checklist authoring guide

**Reason**: Epic 13 specific documentation

---

### 📦 MOVE to features/sandbox-system/ (1 file)

Sandbox feature specific:

1. **sandbox-autonomous-benchmark-guide.md** → Comprehensive sandbox guide

**Reason**: Sandbox-specific guide belongs with sandbox feature

---

### 🗄️ ARCHIVE (1 file)

Temporary documentation:

1. **DOCUMENTATION_CLEANUP_PHASE3_SUMMARY.md** → docs/archive/cleanup-summaries/

**Reason**: Temporary summary from cleanup process, archive for reference

---

### ❓ EVALUATE & DECIDE (3 files)

Need to check if duplicate or still relevant:

1. **benchmarking-philosophy.md**
   - Check if duplicates BENCHMARK_STANDARDS.md
   - If unique, keep or consolidate
   - If duplicate, delete

2. **SCIENTIFIC_METHOD.md**
   - Check if still used/referenced
   - If yes, keep
   - If no, archive

3. **README.md**
   - Superseded by INDEX.md
   - Likely obsolete - DELETE or ARCHIVE

---

## Expected Outcome

**docs/ root will contain**:
- 8 core standards/guides
- Possibly 1-2 additional if SCIENTIFIC_METHOD/benchmarking-philosophy are unique

**Feature folders will contain**:
- All feature-specific migration guides
- All Epic 11 provider abstraction docs
- All feature-specific guides

**Archive will contain**:
- Temporary cleanup summaries
- Any obsolete docs

---

## Execution Plan

1. Create docs/archive/cleanup-summaries/
2. Move 8 files to features/agent-provider-abstraction/
3. Move 1 file to features/prompt-abstraction/
4. Move 2 files to features/document-lifecycle-system/
5. Move 1 file to features/sandbox-system/
6. Archive DOCUMENTATION_CLEANUP_PHASE3_SUMMARY.md
7. Evaluate benchmarking-philosophy.md, SCIENTIFIC_METHOD.md, README.md
8. Commit and push

**Total Files to Move**: 12-15 files
**Expected docs/ root after**: 8-11 files

---

## Benefits

- **Clarity**: docs/ root has only core project-wide documentation
- **Organization**: Feature-specific docs with their features
- **Discoverability**: Easier to find Epic 11 docs in agent-provider-abstraction/
- **Consistency**: All features have same structure (README, PRD, ARCHITECTURE, epics, stories, guides)
