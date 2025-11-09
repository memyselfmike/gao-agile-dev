# Story 1.1: Create Todo

## Story Information
- **Epic**: 1 - Todo Management API
- **Story ID**: 1.1
- **Story Title**: Create Todo
- **Status**: Draft
- **Priority**: P0 (Critical)
- **Assignee**: TBD
- **Estimated Effort**: 2 story points
- **Created**: November 7, 2025

## User Story
**As a** developer using the API  
**I want to** create new todo items  
**So that** I can track tasks that need to be completed

## Description
This story implements the POST /todos endpoint that allows users to create new todo items. The endpoint should accept a JSON payload containing the todo details, validate the input, assign a unique ID and timestamp, then store the todo in memory and return the created object.

## Acceptance Criteria
- [ ] POST /todos endpoint accepts title and description in JSON format
- [ ] Returns 201 status code with the created todo object
- [ ] Assigns unique ID (auto-incrementing integer or UUID)
- [ ] Assigns created_at timestamp automatically
- [ ] Validates required fields (422 for missing title)
- [ ] Validates field constraints (title max 200 chars, description max 1000 chars)
- [ ] Returns proper error responses for invalid input
- [ ] Sets completed field to false by default if not provided
- [ ] Todo object includes all fields: id, title, description, completed, created_at

## Technical Requirements
- Use FastAPI for endpoint implementation
- Use Pydantic models for request/response validation
- Implement proper error handling and HTTP status codes
- Store todos in thread-safe in-memory data structure
- Include comprehensive type hints
- Add docstring documentation

## Definition of Done
- [ ] Endpoint implementation complete
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing
- [ ] Code follows PEP 8 standards
- [ ] Type hints on all functions
- [ ] Error handling implemented
- [ ] Documentation updated
- [ ] Code review completed
- [ ] Test coverage ≥ 70% for this story

## Test Cases

### Happy Path Tests
1. **Valid Todo Creation**
   - Input: `{"title": "Buy groceries", "description": "Milk and bread"}`
   - Expected: 201 status, todo object with ID and timestamp
   
2. **Todo Creation with Minimal Data**
   - Input: `{"title": "Simple task"}`
   - Expected: 201 status, description empty, completed false

### Error Path Tests
1. **Missing Title**
   - Input: `{"description": "No title provided"}`
   - Expected: 422 status, validation error message
   
2. **Title Too Long**
   - Input: `{"title": "a" * 201}`
   - Expected: 422 status, validation error for title length
   
3. **Description Too Long**
   - Input: `{"title": "Valid", "description": "a" * 1001}`
   - Expected: 422 status, validation error for description length

4. **Invalid JSON**
   - Input: Malformed JSON
   - Expected: 400 status, JSON parsing error

## Implementation Notes
- The todo storage should be implemented as a simple in-memory structure (list or dict)
- Use thread-safe operations for concurrent access
- ID generation should be atomic to prevent duplicate IDs
- Timestamp should use ISO 8601 format (datetime.isoformat())
- Consider using a simple counter for ID generation or UUID for uniqueness

## Dependencies
- None (first story in the epic)

## Risks & Assumptions
- **Risk**: Thread safety with in-memory storage
- **Mitigation**: Use proper locking mechanisms or thread-safe data structures
- **Assumption**: In-memory storage is acceptable for this benchmark
- **Assumption**: No persistence required between server restarts

## Example API Usage
```bash
curl -X POST "http://localhost:8000/todos" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Buy groceries",
    "description": "Milk, bread, eggs",
    "completed": false
  }'
```

**Expected Response:**
```json
{
  "id": 1,
  "title": "Buy groceries", 
  "description": "Milk, bread, eggs",
  "completed": false,
  "created_at": "2025-11-07T10:30:00.123456"
}
```

## Story History
- **November 7, 2025**: Story created from Epic 1 requirements