# Story 39.26: Monaco Diff Viewer for Commits

**Story Number**: 39.26
**Epic**: 39.7 - Git Integration & Provider UI
**Feature**: Web Interface
**Status**: Planned
**Priority**: SHOULD HAVE (P1 - V1.1)
**Effort Estimate**: M (Medium - 4 story points)
**Dependencies**: Story 39.25 (Git Timeline), Story 39.12 (Monaco Editor Integration)

---

## User Story

As a **product owner**
I want **to see file diffs for commits in a Monaco diff editor**
So that **I can review changes with syntax highlighting and side-by-side comparison**

---

## Acceptance Criteria

### Diff Panel Navigation
- [ ] AC1: Clicking a commit in timeline (Story 39.25) opens diff panel
- [ ] AC2: Diff panel displays list of changed files with metadata:
  - File name with path
  - Change type badge (Added/Modified/Deleted) with color coding:
    - Added: Green badge
    - Modified: Blue badge
    - Deleted: Red badge
  - Lines changed indicator (+X -Y)
- [ ] AC3: Click file in list to see diff in Monaco diff editor
- [ ] AC4: Navigate between files using "Next" and "Previous" buttons
- [ ] AC5: Keyboard shortcuts: `N` (next file), `P` (previous file), `T` (toggle view)

### Monaco Diff Editor Integration
- [ ] AC6: Diff view defaults to side-by-side mode (original | modified)
- [ ] AC7: Toggle button switches between side-by-side and unified (inline) diff
- [ ] AC8: Syntax highlighting based on file extension (reuse Monaco language detection)
- [ ] AC9: Color coding for changes:
  - Added lines: Green background (#28a74520)
  - Deleted lines: Red background (#f1474720)
  - Modified lines: Yellow background (#ffc10720)
- [ ] AC10: Line numbers displayed on both sides of diff

### Edge Cases & Performance
- [ ] AC11: Binary files show message: "Binary file changed (X bytes → Y bytes)"
- [ ] AC12: Large diffs (>1,000 lines) show warning banner:
  - "Large diff detected (X lines). Performance may be slow."
  - "Expand anyway" button to override
- [ ] AC13: Deleted files show only original content (left side), right side empty
- [ ] AC14: Added files show only new content (right side), left side empty
- [ ] AC15: Diff rendering completes in <500ms for files <1,000 lines

---

## Technical Context

### Architecture Integration

**Integration with Story 39.12 (Monaco Editor)**:
- Reuse Monaco editor instance configuration
- Use Monaco Diff Editor API (`monaco.editor.createDiffEditor()`)
- Leverage syntax highlighting and language detection

**Integration with Epic 27 (GitIntegratedStateManager)**:
- Reuse `GitManager.get_commit_diff()` method
- Leverage `GitManager.get_file_at_revision()` for diff generation

**API Endpoints** (Backend - Story 39.26):
```
GET /api/git/commits/{hash}/diff
Response: {
  files: [
    {
      path: "src/components/GitTimeline.tsx",
      change_type: "modified",
      insertions: 45,
      deletions: 12,
      is_binary: false,
      diff: "@@ -10,3 +10,5 @@\n import { useWebSocket } from '../../hooks';\n+import { CommitCard } from './CommitCard';\n+import { VirtualList } from '../common/VirtualList';\n",
      original_content: "...",  // Full file content at parent commit
      modified_content: "..."   // Full file content at this commit
    }
  ]
}
```

**Frontend Components** (Story 39.26):
```
src/components/git/
├── DiffPanel.tsx            # Main diff panel container
├── FileList.tsx             # List of changed files
├── FileChangeItem.tsx       # Individual file change card
├── MonacoDiffViewer.tsx     # Monaco diff editor wrapper
├── DiffToolbar.tsx          # Toggle buttons, navigation
└── BinaryFileMessage.tsx    # Binary file placeholder
```

### Dependencies

**Story 39.12 (Monaco Editor Integration)**:
- Monaco editor already integrated for file editing
- Reuse Monaco Diff Editor API

**Story 39.25 (Git Timeline)**:
- Commit click handler navigates to diff view
- Commit hash passed as route parameter

**Epic 27 (GitIntegratedStateManager)**:
- `GitManager.get_commit_diff()` - Get diff for commit
- `GitManager.get_file_at_revision()` - Get file content at specific revision

---

## Test Scenarios

### Test 1: Open Diff Panel from Commit
**Given**: User viewing commit timeline
**When**: User clicks commit "abc1234"
**Then**:
- Diff panel opens with commit details at top
- List of changed files displayed (5 files: 3 modified, 1 added, 1 deleted)
- First file automatically selected and diff shown in Monaco editor
- Monaco editor renders in <500ms

### Test 2: Side-by-Side Diff View
**Given**: Diff panel open with modified file selected
**When**: User views default side-by-side diff
**Then**:
- Monaco diff editor shows two panes: Original (left) | Modified (right)
- Added lines highlighted green on right side
- Deleted lines highlighted red on left side
- Modified lines highlighted yellow on both sides
- Syntax highlighting applied (TypeScript in this case)

### Test 3: Unified Diff View
**Given**: Diff panel in side-by-side mode
**When**: User clicks "Toggle View" button (or presses `T`)
**Then**:
- Diff switches to unified (inline) mode
- Added lines show with "+" prefix and green background
- Deleted lines show with "-" prefix and red background
- Modified lines show both old and new inline
- Syntax highlighting preserved

### Test 4: Navigate Between Files
**Given**: Diff panel showing 5 changed files, first file selected
**When**: User clicks "Next" button (or presses `N`)
**Then**:
- Second file selected in file list
- Monaco editor updates to show second file's diff
- Transition smooth (<100ms)
- "Previous" button becomes enabled

### Test 5: Binary File Handling
**Given**: Commit includes binary file (image: logo.png)
**When**: User selects logo.png in file list
**Then**:
- Monaco editor replaced with message: "Binary file changed (1.2 KB → 1.5 KB)"
- Icon indicating binary file type (image icon)
- No diff editor shown
- Navigation buttons still work

### Test 6: Large Diff Warning
**Given**: Commit includes file with 5,000 line diff
**When**: User selects large file
**Then**:
- Warning banner: "Large diff detected (5,000 lines). Performance may be slow."
- "Expand anyway" button shown
- Diff not rendered until user clicks button
- After expand, diff renders (may take 1-2 seconds)

### Test 7: Deleted File Diff
**Given**: Commit deletes file "OldComponent.tsx"
**When**: User selects OldComponent.tsx in file list
**Then**:
- Monaco diff editor shows original content on left
- Right side empty (or grayed out)
- All lines highlighted red (deleted)
- File badge shows "Deleted" in red

### Test 8: Added File Diff
**Given**: Commit adds new file "NewFeature.tsx"
**When**: User selects NewFeature.tsx in file list
**Then**:
- Monaco diff editor shows new content on right
- Left side empty (or grayed out)
- All lines highlighted green (added)
- File badge shows "Added" in green

---

## Definition of Done

### Code Quality
- [ ] Code follows GAO-Dev standards (DRY, SOLID, typed)
- [ ] Type hints throughout (no `any` in TypeScript)
- [ ] structlog for all logging (backend)
- [ ] Error handling comprehensive (try-catch blocks)
- [ ] ESLint + Prettier applied (frontend)
- [ ] Black formatting applied (backend, line length 100)

### Testing
- [ ] Unit tests: 100% coverage for DiffPanel, FileList, MonacoDiffViewer components
- [ ] Integration tests: API endpoint `/api/git/commits/{hash}/diff` tested with mock git repository
- [ ] E2E tests: Playwright test for opening diff, navigating files, toggling view
- [ ] Performance tests: Diff rendering <500ms for files <1,000 lines

### Documentation
- [ ] API documentation: `/api/git/commits/{hash}/diff` endpoint documented
- [ ] Component documentation: MonacoDiffViewer props and usage
- [ ] User guide: How to review commit diffs

### Code Review
- [ ] Code review approved by Winston (Technical Architect)
- [ ] No security vulnerabilities (git operations sandboxed)
- [ ] No regressions (100% existing tests pass)

---

## Implementation Notes

### Backend Implementation (FastAPI)

```python
# gao_dev/web/api/git.py
from fastapi import APIRouter, HTTPException
from pathlib import Path
import structlog

from gao_dev.core.git_manager import GitManager

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/git", tags=["git"])

@router.get("/commits/{commit_hash}/diff")
async def get_commit_diff(commit_hash: str):
    """Get diff for specific commit"""
    try:
        git_manager = GitManager()
        diff_data = git_manager.get_commit_diff(commit_hash)

        files = []
        for file_change in diff_data.files:
            # Detect binary files
            is_binary = _is_binary_file(file_change.path)

            files.append({
                "path": file_change.path,
                "change_type": file_change.change_type,  # added, modified, deleted
                "insertions": file_change.insertions,
                "deletions": file_change.deletions,
                "is_binary": is_binary,
                "diff": file_change.diff if not is_binary else None,
                "original_content": file_change.original_content if not is_binary else None,
                "modified_content": file_change.modified_content if not is_binary else None,
            })

        return {"files": files}
    except Exception as e:
        logger.error("failed_to_get_commit_diff", commit_hash=commit_hash, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to load diff")

def _is_binary_file(file_path: str) -> bool:
    """Detect binary files by extension"""
    binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip', '.tar', '.gz', '.exe', '.dll'}
    return Path(file_path).suffix.lower() in binary_extensions
```

### Frontend Implementation (React + TypeScript + Monaco)

```typescript
// src/components/git/DiffPanel.tsx
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { FileList } from './FileList';
import { MonacoDiffViewer } from './MonacoDiffViewer';
import { DiffToolbar } from './DiffToolbar';
import { BinaryFileMessage } from './BinaryFileMessage';
import type { CommitDiff, FileChange } from '../../types/git';

export const DiffPanel: React.FC = () => {
  const { commitHash } = useParams<{ commitHash: string }>();
  const [selectedFileIndex, setSelectedFileIndex] = useState(0);
  const [viewMode, setViewMode] = useState<'split' | 'unified'>('split');

  const { data, isLoading, error } = useQuery<CommitDiff>({
    queryKey: ['commit-diff', commitHash],
    queryFn: () =>
      fetch(`/api/git/commits/${commitHash}/diff`).then(res => res.json()),
  });

  const selectedFile = data?.files[selectedFileIndex];

  const handleNextFile = () => {
    if (selectedFileIndex < (data?.files.length ?? 0) - 1) {
      setSelectedFileIndex(prev => prev + 1);
    }
  };

  const handlePreviousFile = () => {
    if (selectedFileIndex > 0) {
      setSelectedFileIndex(prev => prev - 1);
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === 'n' || e.key === 'N') handleNextFile();
      if (e.key === 'p' || e.key === 'P') handlePreviousFile();
      if (e.key === 't' || e.key === 'T') setViewMode(prev => prev === 'split' ? 'unified' : 'split');
    };

    window.addEventListener('keypress', handleKeyPress);
    return () => window.removeEventListener('keypress', handleKeyPress);
  }, [selectedFileIndex, data]);

  if (isLoading) return <div>Loading diff...</div>;
  if (error) return <div>Failed to load diff</div>;

  return (
    <div className="diff-panel">
      <DiffToolbar
        viewMode={viewMode}
        onToggleView={() => setViewMode(prev => prev === 'split' ? 'unified' : 'split')}
        onNext={handleNextFile}
        onPrevious={handlePreviousFile}
        hasNext={selectedFileIndex < (data?.files.length ?? 0) - 1}
        hasPrevious={selectedFileIndex > 0}
      />
      <div className="diff-content">
        <FileList
          files={data?.files ?? []}
          selectedIndex={selectedFileIndex}
          onSelectFile={setSelectedFileIndex}
        />
        <div className="diff-viewer">
          {selectedFile?.is_binary ? (
            <BinaryFileMessage file={selectedFile} />
          ) : (
            <MonacoDiffViewer
              file={selectedFile}
              viewMode={viewMode}
            />
          )}
        </div>
      </div>
    </div>
  );
};
```

```typescript
// src/components/git/MonacoDiffViewer.tsx
import React, { useEffect, useRef } from 'react';
import * as monaco from 'monaco-editor';
import type { FileChange } from '../../types/git';

interface MonacoDiffViewerProps {
  file: FileChange | undefined;
  viewMode: 'split' | 'unified';
}

export const MonacoDiffViewer: React.FC<MonacoDiffViewerProps> = ({ file, viewMode }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const editorRef = useRef<monaco.editor.IStandaloneDiffEditor | null>(null);

  useEffect(() => {
    if (!containerRef.current || !file) return;

    // Create Monaco diff editor
    const diffEditor = monaco.editor.createDiffEditor(containerRef.current, {
      enableSplitViewResizing: true,
      renderSideBySide: viewMode === 'split',
      readOnly: true,
      automaticLayout: true,
      scrollBeyondLastLine: false,
      minimap: { enabled: false },
    });

    // Detect language from file extension
    const language = monaco.languages.getLanguages().find(lang =>
      lang.extensions?.includes(file.path.split('.').pop() ?? '')
    )?.id ?? 'plaintext';

    // Set original and modified models
    const originalModel = monaco.editor.createModel(
      file.original_content ?? '',
      language
    );
    const modifiedModel = monaco.editor.createModel(
      file.modified_content ?? '',
      language
    );

    diffEditor.setModel({
      original: originalModel,
      modified: modifiedModel,
    });

    editorRef.current = diffEditor;

    return () => {
      originalModel.dispose();
      modifiedModel.dispose();
      diffEditor.dispose();
    };
  }, [file, viewMode]);

  // Show warning for large diffs
  const isLargeDiff = (file?.insertions ?? 0) + (file?.deletions ?? 0) > 1000;

  return (
    <div className="monaco-diff-viewer">
      {isLargeDiff && (
        <div className="diff-warning">
          Large diff detected ({(file?.insertions ?? 0) + (file?.deletions ?? 0)} lines).
          Performance may be slow.
        </div>
      )}
      <div ref={containerRef} style={{ height: '100%', width: '100%' }} />
    </div>
  );
};
```

```typescript
// src/components/git/FileList.tsx
import React from 'react';
import { FileChangeItem } from './FileChangeItem';
import type { FileChange } from '../../types/git';

interface FileListProps {
  files: FileChange[];
  selectedIndex: number;
  onSelectFile: (index: number) => void;
}

export const FileList: React.FC<FileListProps> = ({ files, selectedIndex, onSelectFile }) => {
  return (
    <div className="file-list">
      {files.map((file, index) => (
        <FileChangeItem
          key={file.path}
          file={file}
          isSelected={index === selectedIndex}
          onClick={() => onSelectFile(index)}
        />
      ))}
    </div>
  );
};
```

```typescript
// src/components/git/FileChangeItem.tsx
import React from 'react';
import { Badge } from '../common/Badge';
import type { FileChange } from '../../types/git';

interface FileChangeItemProps {
  file: FileChange;
  isSelected: boolean;
  onClick: () => void;
}

export const FileChangeItem: React.FC<FileChangeItemProps> = ({ file, isSelected, onClick }) => {
  const changeTypeBadge = {
    added: { label: 'Added', color: 'green' },
    modified: { label: 'Modified', color: 'blue' },
    deleted: { label: 'Deleted', color: 'red' },
  }[file.change_type];

  return (
    <div
      className={`file-change-item ${isSelected ? 'selected' : ''}`}
      onClick={onClick}
    >
      <div className="file-path">{file.path}</div>
      <Badge {...changeTypeBadge} />
      <div className="file-stats">
        +{file.insertions} -{file.deletions}
      </div>
    </div>
  );
};
```

---

## Related Stories

**Dependencies**:
- **Story 39.25**: Git Timeline Commit History (commit selection)
- **Story 39.12**: Monaco Editor Integration (Monaco API)
- **Epic 27**: GitIntegratedStateManager (git diff operations)

**Enables**:
- **Story 39.27**: Git Filters and Search (filtering commits before viewing diff)

---

**Story Owner**: Amelia (Software Developer)
**Reviewer**: Winston (Technical Architect)
**Tester**: Murat (Test Architect)
