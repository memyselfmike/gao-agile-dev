# Interactive Brian Chat - QA Checklist

**Epic**: 30 - Interactive Brian Chat Interface
**Story**: 30.7 - Testing & Documentation
**Version**: 1.0
**Last Updated**: 2025-11-10

---

## Overview

This checklist covers all user paths and edge cases for the Interactive Brian Chat interface. Use this for manual QA validation before marking Epic 30 complete.

**QA Goals**:
- Validate all user scenarios work end-to-end
- Verify error handling is graceful and helpful
- Confirm performance targets are met
- Ensure UX is smooth and intuitive

---

## Pre-QA Setup

### Environment Preparation

- [ ] GAO-Dev installed from latest code (`pip install -e .`)
- [ ] All dependencies installed (including `prompt-toolkit`)
- [ ] API key configured (ANTHROPIC_API_KEY or Ollama running)
- [ ] Clean test environment (fresh terminal)
- [ ] Backup any important work (testing may create test projects)

### Test Projects Preparation

Create these test directories:

```bash
# 1. Existing GAO-Dev project
mkdir -p ~/qa-test/existing-project/.gao-dev
cd ~/qa-test/existing-project
echo "# Test Project" > README.md

# 2. Empty directory (greenfield)
mkdir -p ~/qa-test/new-project

# 3. Existing code without GAO-Dev (brownfield)
mkdir -p ~/qa-test/legacy-app/src
echo "# Legacy App" > ~/qa-test/legacy-app/README.md
echo "flask==2.0.0" > ~/qa-test/legacy-app/requirements.txt
```

---

## PART 1: Core Functionality

### 1.1 REPL Startup

**Test**: Basic startup
```bash
cd ~/qa-test/existing-project
gao-dev start
```

**Expected**:
- [ ] REPL starts within 2 seconds
- [ ] Greeting displays with project name
- [ ] Project status shown (epics, stories, commits if any)
- [ ] Prompt appears: `You: _`
- [ ] No errors in console

**Test**: Startup in empty directory
```bash
cd ~/qa-test/new-project
gao-dev start
```

**Expected**:
- [ ] REPL starts successfully
- [ ] Greenfield message shown
- [ ] Suggests typing 'init'
- [ ] No crash or error

---

### 1.2 Basic Input/Output

**Test**: Simple message
```
You: hello
```

**Expected**:
- [ ] Brian responds (even if "I'm not sure...")
- [ ] Response is formatted in green panel
- [ ] Prompt returns for next input
- [ ] No crash

**Test**: Empty input (just press Enter)
```
You: [Enter]
You: [Enter]
You: [Enter]
```

**Expected**:
- [ ] REPL handles gracefully
- [ ] No error messages
- [ ] Prompt returns immediately

---

### 1.3 Exit Commands

**Test**: Exit variations

Try each exit command in separate sessions:
```
You: exit
You: quit
You: bye
You: goodbye
```

**Expected (for each)**:
- [ ] Farewell message displays
- [ ] Session stats shown (turn count, memory)
- [ ] REPL exits cleanly (return to shell)
- [ ] No errors or crashes

**Test**: Ctrl+D (EOF)
```
[Press Ctrl+D at prompt]
```

**Expected**:
- [ ] Farewell message displays
- [ ] REPL exits gracefully
- [ ] No crash

---

## PART 2: Feature Requests & Workflow Selection

### 2.1 Simple Feature Request

**Test**: Basic feature
```
You: I want to add a search feature
```

**Expected**:
- [ ] "Let me analyze..." acknowledgment appears
- [ ] Analysis completes within 3 seconds
- [ ] Scale level shown (likely Level 2)
- [ ] Project type shown (feature)
- [ ] Reasoning provided
- [ ] Workflows list shown
- [ ] Duration estimate provided
- [ ] Confirmation prompt: "Shall I proceed? (yes/no)"

---

### 2.2 Confirmation Flow

**Test**: User confirms
```
You: I want to add authentication
[Wait for analysis]
You: yes
```

**Expected**:
- [ ] "Great! I'll coordinate..." message
- [ ] Workflow execution begins (or shows it would - may be mocked)
- [ ] Progress updates shown (if execution happens)
- [ ] Completion message (if execution completes)
- [ ] Prompt returns for next input

**Test**: User declines
```
You: I want to build a complex app
[Wait for analysis]
You: no
```

**Expected**:
- [ ] "No problem!" acknowledgment
- [ ] Suggests alternative or asks for clarification
- [ ] Prompt returns for next input
- [ ] No execution happens

---

### 2.3 Multi-Turn Conversation

**Test**: Building context over multiple turns
```
You: I want to build a blog
[Wait for analysis]
You: With Markdown support
[Wait for updated analysis]
You: And syntax highlighting
[Wait for final analysis]
You: yes
```

**Expected**:
- [ ] Each turn builds on previous (context preserved)
- [ ] Final analysis includes all three features
- [ ] Workflows reflect complete scope
- [ ] Brian references previous context in responses

---

## PART 3: Help System

### 3.1 Help Command

**Test**: Basic help
```
You: help
```

**Expected**:
- [ ] Help panel displays immediately (< 100ms)
- [ ] Shows feature request examples
- [ ] Shows project information commands
- [ ] Shows command list (help, exit, etc.)
- [ ] Formatting is clean and readable

---

### 3.2 Contextual Questions

**Test**: Asking questions
```
You: What can you do?
You: How do I create a PRD?
You: What workflows are available?
```

**Expected (for each)**:
- [ ] Relevant answer provided
- [ ] Answer is helpful and actionable
- [ ] No "I don't know" without guidance
- [ ] Prompt returns for next input

---

## PART 4: Initialization Commands

### 4.1 Greenfield Initialization

**Test**: Init new project
```bash
cd ~/qa-test/new-project
gao-dev start
```
```
You: init
[Follow prompts if interactive]
```

**Expected**:
- [ ] Initialization starts
- [ ] Progress messages shown
- [ ] `.gao-dev/` directory created
- [ ] `README.md` created
- [ ] `.gitignore` created (if applicable)
- [ ] Git repository initialized (if applicable)
- [ ] Success message shown
- [ ] Prompt returns for next input

**Verify**:
```bash
ls -la
```
- [ ] `.gao-dev/` exists
- [ ] `README.md` exists
- [ ] Directory structure looks correct

---

### 4.2 Brownfield Initialization

**Test**: Add GAO-Dev to existing project
```bash
cd ~/qa-test/legacy-app
gao-dev start
```
```
You: init
[Follow prompts if interactive]
```

**Expected**:
- [ ] Detects existing project
- [ ] Shows "Adding GAO-Dev tracking..." message
- [ ] `.gao-dev/` directory created
- [ ] Existing files PRESERVED (README.md, requirements.txt)
- [ ] Success message shown
- [ ] Prompt returns for next input

**Verify**:
```bash
ls -la
cat README.md
cat requirements.txt
```
- [ ] `.gao-dev/` exists
- [ ] Existing `README.md` unchanged (or enhanced, not replaced)
- [ ] Existing `requirements.txt` unchanged
- [ ] No files deleted or corrupted

---

### 4.3 Already Initialized

**Test**: Init in directory with existing .gao-dev
```bash
cd ~/qa-test/existing-project
gao-dev start
```
```
You: init
```

**Expected**:
- [ ] Message: "This directory already has a GAO-Dev project"
- [ ] Asks if user wants to reinitialize (or similar)
- [ ] No destructive action without confirmation
- [ ] Prompt returns for next input

---

## PART 5: Session State Management

### 5.1 Session History Tracking

**Test**: Multi-turn session history
```
You: I want to build a blog
You: Add comments to the blog
You: Add user profiles
You: exit
```

**Verify on exit**:
- [ ] Session stats shown
- [ ] Turn count accurate (>= 3)
- [ ] Memory usage shown
- [ ] Session file path shown

**Verify after exit**:
```bash
ls .gao-dev/
cat .gao-dev/last_session_history.json
```
- [ ] `last_session_history.json` exists
- [ ] Contains conversation history (check file is not empty)

---

### 5.2 Session Restoration (Partial - Awareness)

**Test**: Restart after session
```bash
gao-dev start
```

**Expected**:
- [ ] REPL starts
- [ ] Message about previous session (if file exists)
- [ ] Can start fresh conversation
- [ ] No errors loading previous session

**Note**: Full auto-restore may not be implemented in v1.0. Just verify no crash if session file exists.

---

## PART 6: Error Handling & Recovery

### 6.1 Unclear Input

**Test**: Gibberish input
```
You: asdfqwer zxcv
```

**Expected**:
- [ ] Brian responds (doesn't crash)
- [ ] Message: "I'm not sure what you mean..."
- [ ] Suggestions for how to rephrase
- [ ] Prompt returns for next input

---

### 6.2 Analysis Failures

**Test**: Request that might cause analysis error

(This may be hard to trigger. Try disconnecting network or using invalid API key)

```
You: Build something complex
```

**Expected** (if analysis fails):
- [ ] Error message displayed
- [ ] Message is helpful and actionable
- [ ] Suggests rephrasing or trying again
- [ ] REPL continues (no crash)
- [ ] Prompt returns for next input

---

### 6.3 Execution Failures

**Test**: Confirm a workflow that might fail

(Hard to test without real workflow execution)

**Expected** (if execution fails):
- [ ] Error message displayed
- [ ] Details about what failed
- [ ] Suggests next steps
- [ ] REPL continues (no crash)
- [ ] Prompt returns for next input

---

## PART 7: Cancellation & Interruption

### 7.1 Ctrl+C During Execution

**Test**: Cancel during workflow execution
```
You: Build a complex application
[Wait for analysis]
You: yes
[Press Ctrl+C during execution]
```

**Expected**:
- [ ] Cancellation message: "Operation cancelled by user"
- [ ] REPL continues (does NOT exit)
- [ ] Prompt returns for next input
- [ ] No crash or hang

---

### 7.2 Ctrl+C at Prompt

**Test**: Ctrl+C while waiting for input
```
You: [Press Ctrl+C]
```

**Expected**:
- [ ] Cancellation message or new prompt
- [ ] REPL continues (does NOT exit)
- [ ] No crash

---

### 7.3 Recovery After Cancellation

**Test**: Continue working after Ctrl+C
```
You: Build something big
You: yes
[Press Ctrl+C]
You: Actually, I want to do something small instead
```

**Expected**:
- [ ] Cancellation handled
- [ ] New request processed normally
- [ ] No lingering state issues
- [ ] Brian responds to new request

---

## PART 8: Performance Validation

### 8.1 Startup Performance

**Test**: Measure startup time

```bash
time gao-dev start
[Type 'exit' immediately]
```

**Expected**:
- [ ] Total time < 2 seconds
- [ ] Greeting appears quickly
- [ ] No long pauses

---

### 8.2 Response Performance

**Test**: Measure analysis time

(Use stopwatch or `time` command)

```
You: I want to add authentication
[Measure time from Enter to "Shall I proceed?"]
```

**Expected**:
- [ ] First analysis: < 3 seconds (with AI processing)
- [ ] Subsequent analyses: < 1 second (caching)
- [ ] Help command: < 100ms (instant)

---

### 8.3 Memory Usage

**Test**: Long session memory

Run a session with 20+ turns, then check memory:

**On Linux/Mac**:
```bash
ps aux | grep "gao-dev start"
```

**On Windows**:
```powershell
Get-Process | Where-Object {$_.ProcessName -like "*python*"}
```

**Expected**:
- [ ] Memory usage < 100 MB for typical session (< 20 turns)
- [ ] Memory usage < 200 MB for long session (> 50 turns)
- [ ] No memory leaks (memory doesn't continuously grow)

---

## PART 9: User Experience

### 9.1 Formatting & Readability

**Test**: Visual inspection

Throughout all tests, check:

- [ ] All panels display correctly (no broken borders)
- [ ] Colors are readable (green for Brian, red for errors, etc.)
- [ ] Markdown rendering works (bold, lists, code blocks)
- [ ] No text overflow or wrapping issues
- [ ] Spacing and padding looks professional

---

### 9.2 Message Clarity

**Test**: Message quality review

Check that Brian's messages:

- [ ] Are clear and concise (not too verbose)
- [ ] Use natural language (not robotic)
- [ ] Provide actionable guidance
- [ ] Include context when referencing previous turns
- [ ] Have proper grammar and spelling

---

### 9.3 Input History

**Test**: Arrow key navigation
```
You: first message
You: second message
You: third message
[Press Up Arrow]
[Press Up Arrow]
[Press Up Arrow]
```

**Expected**:
- [ ] Up arrow shows previous inputs in reverse order
- [ ] Down arrow shows next inputs
- [ ] Can edit recalled input
- [ ] History persists for session duration

---

## PART 10: Integration with Existing System

### 10.1 CLI Compatibility

**Test**: Other CLI commands still work

```bash
gao-dev --help
gao-dev health
gao-dev list-workflows
gao-dev list-agents
```

**Expected** (for each):
- [ ] Command works as before
- [ ] No breaking changes
- [ ] Output is correct

---

### 10.2 State Sharing

**Test**: REPL aware of CLI changes

```bash
# Create an epic via CLI
gao-dev state create-epic 99 "Test Epic"

# Start REPL
gao-dev start
```
```
You: What's the status?
```

**Expected**:
- [ ] Epic 99 appears in status
- [ ] REPL sees changes made via CLI
- [ ] State is shared via `.gao-dev/documents.db`

---

## PART 11: Edge Cases

### 11.1 Very Long Input

**Test**: Input > 1000 characters
```
You: [Paste a very long message, e.g., 2000 characters]
```

**Expected**:
- [ ] Input accepted (no truncation)
- [ ] Brian processes it
- [ ] No crash or hang

---

### 11.2 Special Characters

**Test**: Input with special characters
```
You: I want to add @mention and #hashtag support
You: Fix bug with $pecial ch@racters
```

**Expected**:
- [ ] Input handled correctly
- [ ] No parsing errors
- [ ] Brian responds appropriately

---

### 11.3 Rapid Input

**Test**: Multiple commands quickly
```
You: hello
You: help
You: status
You: exit
[Type all quickly without waiting]
```

**Expected**:
- [ ] All inputs processed in order
- [ ] No commands dropped
- [ ] No race conditions
- [ ] Clean exit

---

## PART 12: Final Integration Test

### 12.1 Complete User Journey (New User)

**Scenario**: Brand new user, first time using GAO-Dev

**Steps**:
1. Create empty directory
2. Start REPL
3. Type 'init'
4. Request first feature
5. Confirm and execute
6. Exit

**Checklist**:
- [ ] Startup smooth and fast
- [ ] Greenfield message clear
- [ ] Initialization successful
- [ ] Feature request analyzed correctly
- [ ] Workflows execute (or mock execution shown)
- [ ] Exit graceful
- [ ] Overall experience feels polished

**Time**: Should complete in < 5 minutes

---

### 12.2 Complete User Journey (Experienced User)

**Scenario**: Experienced user adding feature to existing project

**Steps**:
1. Navigate to existing project
2. Start REPL
3. Review status
4. Request new feature
5. Refine over 2-3 turns
6. Confirm execution
7. Cancel with Ctrl+C
8. Try different approach
9. Exit

**Checklist**:
- [ ] Status accurate
- [ ] Multi-turn refinement works
- [ ] Context preserved
- [ ] Ctrl+C cancellation graceful
- [ ] Recovery smooth
- [ ] Exit saves session
- [ ] Overall experience professional

**Time**: Should complete in < 10 minutes

---

## QA Sign-Off

### Test Results Summary

**Total Tests Executed**: ___ / ___
**Tests Passed**: ___ / ___
**Tests Failed**: ___ / ___
**Blockers Found**: ___ (list below)

### Blockers (P0 - Must Fix)

1. _____________________________
2. _____________________________
3. _____________________________

### Issues (P1 - Should Fix)

1. _____________________________
2. _____________________________
3. _____________________________

### Nice-to-Haves (P2 - Future)

1. _____________________________
2. _____________________________
3. _____________________________

### Performance Results

| Metric | Target | Actual | Pass/Fail |
|--------|--------|--------|-----------|
| Startup time | < 2s | ___s | ___ |
| First analysis | < 3s | ___s | ___ |
| Subsequent analysis | < 1s | ___s | ___ |
| Memory usage (20 turns) | < 100 MB | ___ MB | ___ |
| Memory usage (50 turns) | < 200 MB | ___ MB | ___ |

### Overall Assessment

- [ ] **APPROVED** - Ready for production (all P0 tests pass, performance targets met)
- [ ] **APPROVED WITH NOTES** - Ready with minor known issues (documented above)
- [ ] **REJECTED** - Not ready (blockers present, needs more work)

### QA Engineer Sign-Off

**Name**: _____________________________
**Date**: _____________________________
**Signature**: _____________________________

---

## Notes for Future Testing

### Test Environment Variations

Consider testing on:
- [ ] Windows 10/11
- [ ] macOS (Intel and Apple Silicon)
- [ ] Linux (Ubuntu, Fedora, Arch)
- [ ] Different terminal emulators (Windows Terminal, iTerm2, GNOME Terminal)
- [ ] Different Python versions (3.11, 3.12, 3.13)

### Load Testing (Future)

For production deployment, consider:
- [ ] 100+ turn sessions
- [ ] Multiple concurrent REPL sessions
- [ ] Very large projects (1000+ epics)
- [ ] Network failures during API calls
- [ ] Disk full scenarios

---

**Version**: 1.0
**Last Updated**: 2025-11-10
**Next Review**: After Epic 30 completion
