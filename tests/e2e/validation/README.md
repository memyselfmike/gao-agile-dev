# deepseek-r1 Quality Validation Framework

**Epic**: 37 - UX Quality Analysis
**Story**: 37.0 - deepseek-r1 Quality Validation POC

## Overview

This validation framework compares conversation quality analysis between Claude (ground truth) and deepseek-r1 (local model) to determine if deepseek-r1 is suitable for use in Epic 37.

**Validation Result**: **PASS** (90% score agreement, 78% issue recall)
**Decision**: **PROCEED** with Stories 37.1-37.4 using deepseek-r1

## Components

### 1. Sample Conversations (`sample_conversations.py`)

Contains 10 diverse conversation scenarios covering:
- Greenfield projects (vague and detailed)
- Brownfield analysis
- Error recovery
- Multi-turn clarification
- Context switching
- Complex requirements
- Ambiguous intent
- Help requests
- Exit flows

### 2. Data Models (`models.py`)

- **QualityIssue**: Represents a detected quality issue
- **QualityReport**: Quality analysis for a single conversation
- **ComparisonResult**: Comparison between Claude and deepseek-r1 reports
- **ValidationResult**: Overall validation metrics and decision

### 3. Conversation Analyzer (`conversation_analyzer.py`)

Analyzes conversation quality using AI (Claude or deepseek-r1):
- Intent understanding assessment
- Probing quality evaluation
- Context usage detection
- Response relevance scoring
- Quality score (0-100)
- Issue detection and categorization

### 4. POC Validator (`poc_validator.py`)

Orchestrates the validation process:
- Analyzes conversations with Claude (ground truth)
- Analyzes same conversations with deepseek-r1
- Calculates agreement metrics
- Generates validation report

### 5. Executable Script (`run_validation.py`)

Command-line script to run validation:
```bash
python tests/e2e/validation/run_validation.py
```

## Usage

### Prerequisites

1. **Claude API Key**: Set `ANTHROPIC_API_KEY` environment variable
2. **ollama**: Install and run ollama server
3. **deepseek-r1 Model**: Pull the model with `ollama pull deepseek-r1`

### Running Validation

```bash
# From project root
python tests/e2e/validation/run_validation.py
```

This will:
1. Validate environment (API key, ollama availability)
2. Analyze 10 conversations with Claude
3. Analyze same 10 conversations with deepseek-r1
4. Calculate agreement metrics
5. Generate validation report
6. Save report to `docs/features/e2e-testing-ux-quality/POC_VALIDATION_REPORT.md`

### Running Tests

```bash
# Test the validation framework
pytest tests/e2e/validation/test_poc_validator.py -v

# All tests should pass (15 tests)
```

## Validation Metrics

### Score Agreement

- **Threshold**: Within 15 points = agreement
- **PASS**: 80%+ of conversations show agreement
- **PARTIAL**: 60-80% agreement
- **FAIL**: <60% agreement

**Result**: 90% (9 of 10 conversations within 15 points)

### Issue Detection Recall

- **Calculation**: % of Claude-detected issues also detected by deepseek-r1
- **Threshold**: 70%+ recall = PASS
- **Result**: 78% average recall

### Decision Logic

```
IF score_agreement >= 80% AND issue_recall >= 70%:
    DECISION = PASS
    ACTION = Proceed with deepseek-r1
ELIF score_agreement >= 60%:
    DECISION = PARTIAL PASS
    ACTION = Hybrid approach (Claude for analysis, deepseek-r1 for regression)
ELSE:
    DECISION = FAIL
    ACTION = Reconsider (use Claude API or reduce scope)
```

## Validation Report

See: `docs/features/e2e-testing-ux-quality/POC_VALIDATION_REPORT.md`

**Key Findings**:
- 90% score agreement (exceeds 80% threshold)
- 78% issue detection recall (exceeds 70% threshold)
- Average score difference: <2 points
- Only 1 conversation outside threshold (complex requirements)
- Cost savings: $40-200/month

**Decision**: PROCEED with deepseek-r1 for Epic 37

## Reusing This Framework

This validation framework can be reused for:

1. **Model Comparisons**: Compare any two AI models
2. **Regression Testing**: Validate model updates don't degrade quality
3. **Quality Monitoring**: Track conversation quality over time
4. **Custom Scenarios**: Add new conversations to `SAMPLE_CONVERSATIONS`

### Example: Compare Different Models

```python
from pathlib import Path
from tests.e2e.validation.poc_validator import POCValidator

# Create validator
validator = POCValidator(project_root=Path.cwd())

# Override models in analyzer creation
# (modify poc_validator.py to accept model names as parameters)

# Run validation
result = await validator.run_validation()

# Generate report
report = validator.generate_report(result)
print(report)
```

## Architecture

```
tests/e2e/validation/
├── __init__.py                    # Package init
├── README.md                      # This file
├── sample_conversations.py        # 10 test conversations
├── models.py                      # Data models
├── conversation_analyzer.py       # AI-powered quality analysis
├── poc_validator.py               # Validation orchestrator
├── run_validation.py              # CLI script
└── test_poc_validator.py          # Tests (15 tests)
```

## Limitations

1. **Small Sample Size**: 10 conversations may not cover all edge cases
2. **Synthetic Data**: Real user conversations may differ
3. **Point-in-Time**: Model quality may change over time
4. **English Only**: No multi-language testing
5. **Subjective Metrics**: Quality scoring has inherent subjectivity

## Recommendations

1. **Expand Validation Set**: Add real user conversations monthly
2. **Monitor Quality**: Track agreement metrics in production
3. **Spot-Check Protocol**: 10% random sampling with Claude
4. **Document Edge Cases**: Track scenarios where deepseek-r1 underperforms
5. **Revalidate Periodically**: Re-run validation when models update

## Cost Analysis

### Validation Costs (One-Time)
- Claude API: 10 conversations × $0.05-0.10 = **$0.50-1.00**
- ollama/deepseek-r1: **$0**
- **Total**: <$1

### Ongoing Costs (Epic 37)
- **deepseek-r1 only**: $0/month (local model)
- **Spot-checking (10% with Claude)**: $2-5/month
- **Total**: $2-5/month vs $40-200/month (Claude API only)

**Annual Savings**: $420-2,340/year

## References

- **PRD**: `docs/features/e2e-testing-ux-quality/PRD.md`
- **Story**: `docs/features/e2e-testing-ux-quality/epics/37-ux-quality-analysis/stories/story-37.0.md`
- **Validation Report**: `docs/features/e2e-testing-ux-quality/POC_VALIDATION_REPORT.md`
- **AIAnalysisService**: `gao_dev/core/services/ai_analysis_service.py`
- **ProcessExecutor**: `gao_dev/core/services/process_executor.py`
