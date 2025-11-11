# Migration Guide: Feature-Based Document Structure

**Version:** 1.0
**Epic:** 32-34 - Feature-Based Document Structure
**Last Updated:** 2025-11-11

## Overview

This guide helps you migrate existing GAO-Dev projects to the new feature-based document structure introduced in Epics 32-34.

The feature-based structure provides:
- **Co-located epic-story organization** - Stories live inside their epic folders
- **Feature isolation** - Each feature has its own self-contained folder
- **Scalable hierarchy** - Clean separation from MVP to feature to epic to story
- **Automatic validation** - Built-in structure compliance checking

---

## When to Migrate

### New Projects
**Use feature-based structure from the start:**
```bash
gao-dev create-feature mvp --scope mvp --scale-level 4
```

### Existing Projects
**Migration is optional.** The existing structure continues working (backward compatible).

Consider migrating if:
- You have multiple features and want better organization
- You want co-located epic-story structure
- You want automatic validation

---

## Migration Steps

### Step 1: Run Database Migration

Apply the features table migration:

```bash
# Apply migration
gao-dev migrate

# Verify migration applied
gao-dev list-features  # Should return empty list (no features yet)
```

**What this does:**
- Creates `features` table in `.gao-dev/documents.db`
- Adds feature state tracking
- No changes to existing files

### Step 2: Create Features for Existing Work

If you have existing documentation in `docs/`:

```bash
# For greenfield projects - create MVP feature
gao-dev create-feature mvp --scope mvp --scale-level 4

# For specific features
gao-dev create-feature user-auth --scope feature --scale-level 3
gao-dev create-feature payments --scope feature --scale-level 3
```

**Options:**
- `--scope`: `mvp`, `feature`, `enhancement`, `spike`
- `--scale-level`: `2` (small), `3` (medium), `4` (greenfield)
- `--description`: Optional feature description
- `--owner`: Optional owner name

### Step 3: Migrate Documents

#### Option A: Manual Migration (Recommended for small projects)

**For MVP:**
```bash
# Create feature structure
gao-dev create-feature mvp --scope mvp --scale-level 4

# Move existing docs to feature folder
mv docs/PRD.md docs/features/mvp/PRD.md
mv docs/ARCHITECTURE.md docs/features/mvp/ARCHITECTURE.md
mv docs/epics docs/features/mvp/epics

# Create README.md (will be auto-generated in future)
# The create-feature command already created this

# Commit changes
git add docs/features/mvp
git commit -m "refactor: migrate to feature-based structure"
```

**For additional features:**
```bash
# Create feature
gao-dev create-feature user-auth --scale-level 3

# Move feature-specific docs
mv docs/user-auth/* docs/features/user-auth/
```

#### Option B: Automated Migration (Future)

```bash
# Not yet implemented (planned for Epic 35)
gao-dev migrate-feature --from docs/ --to docs/features/mvp/
```

### Step 4: Migrate Epics to Co-Located Structure

The new structure uses co-located epic-story folders:

**Old Structure:**
```
docs/
├── epics/
│   └── epic-1.md
└── stories/
    ├── story-1.1.md
    └── story-1.2.md
```

**New Structure:**
```
docs/features/mvp/
└── epics/
    └── 1-epic-name/
        ├── README.md          # Epic definition
        ├── stories/
        │   ├── story-1.1.md
        │   └── story-1.2.md
        └── context/           # Context XML files
```

**Migration script:**
```bash
# Create epic folder
mkdir -p docs/features/mvp/epics/1-foundation/stories
mkdir -p docs/features/mvp/epics/1-foundation/context

# Move epic README
mv docs/epics/epic-1.md docs/features/mvp/epics/1-foundation/README.md

# Move stories
mv docs/stories/story-1.* docs/features/mvp/epics/1-foundation/stories/

# Commit
git add docs/features/mvp/epics
git rm -r docs/stories
git commit -m "refactor: migrate to co-located epic-story structure"
```

### Step 5: Validate Structure

Check compliance with new structure:

```bash
# Validate specific feature
gao-dev validate-structure --feature mvp

# Validate all features
gao-dev validate-structure --all

# Fix any violations reported
```

**Common violations:**
- Missing README.md
- Old `stories/` folder at root (should be co-located inside epics)
- Missing required folders (`epics/`, `QA/`)

---

## Before and After

### Before (Legacy Structure)

```
docs/
├── PRD.md
├── ARCHITECTURE.md
├── epics/
│   ├── epic-1.md
│   └── epic-2.md
└── stories/
    ├── story-1.1.md
    ├── story-1.2.md
    └── story-2.1.md
```

### After (Feature-Based Structure)

```
docs/features/
├── mvp/                              # Greenfield initial scope
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── README.md                     # Feature overview
│   ├── CHANGELOG.md
│   ├── MIGRATION_GUIDE.md
│   │
│   ├── epics/                        # Co-located epic-story structure
│   │   ├── 1-foundation/            # Epic 1 (number + name)
│   │   │   ├── README.md            # Epic definition
│   │   │   ├── stories/             # Stories for Epic 1
│   │   │   │   ├── story-1.1.md
│   │   │   │   └── story-1.2.md
│   │   │   └── context/             # Context XML
│   │   │       └── story-1.1.xml
│   │   │
│   │   └── 2-advanced/              # Epic 2
│   │       ├── README.md
│   │       └── stories/
│   │           └── story-2.1.md
│   │
│   ├── QA/                          # Quality artifacts
│   ├── retrospectives/              # Retrospectives
│   └── ceremonies/                  # Level 4 only
│
└── user-auth/                       # Subsequent feature
    ├── PRD.md
    ├── ARCHITECTURE.md
    ├── README.md
    ├── CHANGELOG.md
    ├── epics/
    │   └── 1-oauth/
    │       ├── README.md
    │       └── stories/
    ├── QA/
    └── retrospectives/
```

---

## Common Issues

### Issue 1: "Feature already exists"

**Cause:** Feature folder or DB record already exists

**Fix:**
```bash
# Check existing features
gao-dev list-features

# If orphaned, remove and recreate
rm -rf docs/features/mvp/
sqlite3 .gao-dev/documents.db "DELETE FROM features WHERE name='mvp';"
gao-dev create-feature mvp --scope mvp --scale-level 4
```

### Issue 2: Structure validation fails

**Cause:** Missing required files or folders

**Fix:**
```bash
# Check violations
gao-dev validate-structure --feature mvp

# Add missing files/folders as reported
mkdir -p docs/features/mvp/QA
mkdir -p docs/features/mvp/retrospectives
touch docs/features/mvp/README.md
```

### Issue 3: Old stories/ folder detected

**Cause:** Stories at feature root instead of co-located in epics

**Fix:**
```bash
# Move stories to correct epic location
mv docs/features/mvp/stories/story-1.* docs/features/mvp/epics/1-epic-name/stories/

# Remove old stories folder
rmdir docs/features/mvp/stories
```

### Issue 4: Git conflicts during migration

**Cause:** Multiple people migrating simultaneously

**Fix:**
```bash
# Coordinate migration timing
# One person migrates, others pull changes

# If conflicts occur:
git status
git add .
git commit -m "refactor: complete feature-based migration"
```

---

## Rollback

If you need to rollback migration:

### Rollback Database Migration

```bash
# Rollback database changes
gao-dev migrate --rollback

# Verify rollback
sqlite3 .gao-dev/documents.db ".tables"  # features table should be gone
```

### Rollback File Structure

```bash
# Remove feature folders (if desired)
rm -rf docs/features/

# Restore old structure from git
git checkout -- docs/
```

### Continue Using Legacy Structure

The system is backward compatible - you can continue using:
```
docs/
├── PRD.md
├── ARCHITECTURE.md
├── epics.md
└── stories/
    └── story-*.md
```

---

## Validation Checklist

After migration, verify:

- [ ] All features created: `gao-dev list-features`
- [ ] All feature folders have required structure: `gao-dev validate-structure --all`
- [ ] All PRDs migrated to `docs/features/{name}/PRD.md`
- [ ] All architectures migrated to `docs/features/{name}/ARCHITECTURE.md`
- [ ] All epics in `docs/features/{name}/epics/{num}-{name}/`
- [ ] All stories co-located in `docs/features/{name}/epics/{num}-{name}/stories/`
- [ ] No old `docs/stories/` folder at root
- [ ] Git working tree clean: `git status`
- [ ] All tests passing: `pytest`

---

## Support

For issues or questions:

1. **Check validation output:** `gao-dev validate-structure --all`
2. **Review CLAUDE.md** for updated commands
3. **Check feature documentation:** `docs/features/feature-based-document-structure/`
4. **Run health check:** `gao-dev health`

---

## Next Steps

After successful migration:

1. **Update workflows:** Feature-scoped workflows now resolve `{{feature_name}}`
2. **Use new commands:**
   - `gao-dev create-feature` for new features
   - `gao-dev list-features` to see all features
   - `gao-dev validate-structure` to check compliance
3. **Enjoy benefits:**
   - Better organization
   - Scalable structure
   - Automatic validation
   - Clear feature isolation

---

**Migration completed?** Welcome to the feature-based document structure!
