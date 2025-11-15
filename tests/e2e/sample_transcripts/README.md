# Sample Conversation Transcripts

**Story**: 37.1 - Conversation Instrumentation
**Epic**: 37 - UX Quality Analysis
**Purpose**: Validation data for quality analysis implementation

## Overview

This directory contains sample conversation transcripts that demonstrate various conversation patterns and scenarios for UX quality analysis validation.

These transcripts are used by Story 37.2 (Quality Analysis) to validate the analysis algorithms and UX issue detection.

## Transcript Files

### 1. `greenfield_vague_to_detailed.json`
**Type**: Greenfield project initiation
**Scenario**: User starts with vague idea and Brian clarifies through questions
**Turns**: 5
**Key Features**:
- Progressive clarification
- Vision elicitation workflow selection
- Context evolution (no context → pending confirmation)
- Scale-adaptive routing (Level 4)

**Use Cases**:
- Validate clarification effectiveness
- Test workflow selection logic
- Analyze question quality
- Measure time to actionable requirements

---

### 2. `brownfield_analysis.json`
**Type**: Brownfield enhancement
**Scenario**: Adding authentication to existing Flask app
**Turns**: 4
**Key Features**:
- Codebase analysis
- Technical requirements gathering
- Epic/story breakdown
- Context evolution (story selection)

**Use Cases**:
- Validate brownfield detection
- Test integration analysis
- Analyze technical guidance quality
- Measure implementation readiness

---

### 3. `error_recovery.json`
**Type**: Error recovery
**Scenario**: User provides incomplete commands, Brian recovers gracefully
**Turns**: 5
**Key Features**:
- Ambiguous input handling
- Progressive context building
- Multiple recovery attempts
- Eventually successful workflow initiation

**Use Cases**:
- Validate error handling
- Test recovery strategies
- Analyze clarification prompts
- Measure resilience

---

### 4. `multi_turn_clarification.json`
**Type**: Multi-turn clarification
**Scenario**: User starts with "build me something" and Brian extracts full requirements
**Turns**: 6
**Key Features**:
- Extreme vagueness → full specification
- Step-by-step requirement extraction
- Similar product references
- Final workflow initiation

**Use Cases**:
- Validate extreme vagueness handling
- Test questioning strategy
- Analyze conversation depth
- Measure clarification efficiency

---

### 5. `help_request.json`
**Type**: Help and education
**Scenario**: User explores GAO-Dev capabilities through help commands
**Turns**: 6
**Key Features**:
- Help system
- Educational responses
- Capability discovery
- Transition to productive work

**Use Cases**:
- Validate help quality
- Test educational effectiveness
- Analyze onboarding experience
- Measure learning curve

## JSON Format

All transcripts follow the standard format from Story 36.2:

```json
[
  {
    "timestamp": "ISO 8601 timestamp",
    "user_input": "User's message",
    "brian_response": "Brian's complete response",
    "context_used": {
      "project_root": "/path/to/project",
      "session_id": 12345,
      "current_epic": null,
      "current_story": null,
      "pending_confirmation": false
    }
  }
]
```

## Validation

All transcripts have been validated using `TranscriptValidator`:

```python
from tests.e2e.harness.transcript_validator import TranscriptValidator

validator = TranscriptValidator(Path("greenfield_vague_to_detailed.json"))
validator.load_transcript()
validator.validate_all()  # Passes format and content validation
summary = validator.generate_summary()
```

## Usage in Quality Analysis

These transcripts are used by Story 37.2 to validate:

1. **Conversation Flow Analysis**
   - Turn progression logic
   - Clarification patterns
   - Recovery strategies

2. **UX Issue Detection**
   - Confusion indicators
   - Repetitive questions
   - Dead ends
   - User frustration patterns

3. **Response Quality Metrics**
   - Clarity scores
   - Helpfulness ratings
   - Completeness checks

4. **Context Management**
   - Context evolution
   - State tracking
   - Confirmation handling

## Adding New Transcripts

To add new sample transcripts:

1. **Capture**: Run ChatREPL with `--capture-mode` flag
2. **Validate**: Use `TranscriptValidator` to ensure format compliance
3. **Document**: Add entry to this README with scenario description
4. **Commit**: Sample transcripts are committed (not gitignored)

Example:
```bash
gao-dev start --capture-mode
# ... have conversation ...
# Transcript saved to .gao-dev/test_transcripts/session_TIMESTAMP.json

# Validate
python -c "
from pathlib import Path
from tests.e2e.harness.transcript_validator import TranscriptValidator
validator = TranscriptValidator(Path('.gao-dev/test_transcripts/session_TIMESTAMP.json'))
validator.validate_all()
validator.print_summary()
"

# Copy to sample_transcripts
cp .gao-dev/test_transcripts/session_TIMESTAMP.json tests/e2e/sample_transcripts/my_scenario.json
```

## Statistics

| Transcript | Turns | Duration | Avg Turn Time | User Chars | Brian Chars |
|-----------|-------|----------|---------------|------------|-------------|
| greenfield_vague_to_detailed | 5 | ~292s | ~58s | 387 | 2,847 |
| brownfield_analysis | 4 | ~210s | ~52s | 312 | 2,456 |
| error_recovery | 5 | ~285s | ~57s | 189 | 2,234 |
| multi_turn_clarification | 6 | ~240s | ~40s | 278 | 3,012 |
| help_request | 6 | ~255s | ~42s | 234 | 3,456 |
| **TOTAL** | **26** | **~1282s** | **~49s** | **1,400** | **14,005** |

## Quality Benchmarks

These transcripts establish quality benchmarks for:

- **Response Time**: Avg ~50s per turn (simulated thinking time)
- **Response Length**: Avg ~540 chars per Brian response
- **Clarification Rate**: ~60% of turns include clarifying questions
- **Success Rate**: 100% reach productive workflow initiation
- **Context Changes**: Avg 1.2 context changes per conversation

## Notes

- **Not Real Data**: These are synthetic transcripts created for validation
- **Idealized Flow**: Represent successful conversation patterns
- **Committed to Git**: Unlike production transcripts (gitignored)
- **Used by Tests**: Story 37.2 tests import these directly

## References

- Story 36.2: Capture mode implementation
- Story 37.1: Conversation instrumentation testing
- Story 37.2: Quality analysis (consumer of these transcripts)
