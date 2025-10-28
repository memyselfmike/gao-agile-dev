# Story 6.2: Story-Based Config Format

**Epic**: Epic 6 - Incremental Story-Based Workflow
**Status**: Done
**Priority**: P0 (Critical)
**Estimated Effort**: 5 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-28
**Completed**: 2025-10-28

## User Story

**As a** benchmark configuration author  
**I want** to define epics and stories in the benchmark YAML  
**So that** the system can iterate through stories one at a time

## Acceptance Criteria

- Extended config schema with epics[] and stories[]
- Story definition includes: name, agent, acceptance_criteria
- Backward compatible with existing phase-based configs
- Config validator updated for new format

## Definition of Done

- Config schema extended
- Backward compatibility maintained
- Example configs created
- Documentation updated
