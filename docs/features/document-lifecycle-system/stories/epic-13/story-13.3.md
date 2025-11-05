# Story 13.3: Query Reference Resolver (@query:)

**Epic:** 13 - Meta-Prompt System & Context Injection
**Story Points:** 4
**Priority:** P1
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Implement @query: reference resolver for injecting database query results into prompts. This enables dynamic data injection such as story lists, epic progress, and state information directly into agent prompts.

---

## Business Value

This story enables data-driven prompts:

- **Dynamic Context**: Prompts always include current state information
- **Query Results**: Inject filtered story lists, epic progress, sprint velocity
- **Formatted Output**: Query results formatted as markdown tables
- **Safe Queries**: SQL injection prevention with whitelisted tables/columns
- **Performance**: Fast queries (<100ms) suitable for prompt generation

---

## Acceptance Criteria

### Query Syntax
- [ ] SQL-like query syntax: `@query:stories.where(epic=3, status='done')`
- [ ] Support tables: stories, epics, sprints, documents
- [ ] Support filters: where(), order_by(), limit()
- [ ] Query validation before execution
- [ ] Whitelist of allowed tables and columns

### Format Options
- [ ] `format('markdown')` - Markdown table output (default)
- [ ] `format('json')` - JSON array output
- [ ] `format('csv')` - CSV output
- [ ] `format('list')` - Bullet list output
- [ ] Custom format templates supported

### Query Builder
- [ ] `QueryBuilder` class translates DSL to SQL
- [ ] Parameter binding prevents SQL injection
- [ ] Support for common patterns (completed stories, blocked stories, etc.)
- [ ] Convenience methods: `get_epic_progress()`, `get_sprint_velocity()`

### Safety & Performance
- [ ] Query result size limit (max 1000 chars, configurable)
- [ ] Query timeout (max 5 seconds)
- [ ] Only SELECT queries allowed (no INSERT/UPDATE/DELETE)
- [ ] Performance: Query execution <100ms

---

## Technical Notes

### Implementation

```python
# gao_dev/core/meta_prompts/resolvers/query_resolver.py

from typing import List, Dict, Any
from gao_dev.core.meta_prompts.reference_resolver import ReferenceResolver

class QueryResolver(ReferenceResolver):
    """Resolver for @query: references."""

    ALLOWED_TABLES = {'stories', 'epics', 'sprints', 'documents'}
    ALLOWED_COLUMNS = {
        'stories': {'id', 'epic_num', 'story_num', 'title', 'status', 'priority', 'points', 'owner'},
        'epics': {'id', 'epic_num', 'name', 'status', 'total_points', 'completed_points'},
        'sprints': {'id', 'sprint_num', 'name', 'status', 'start_date', 'end_date'},
        'documents': {'id', 'path', 'type', 'state', 'author', 'owner'}
    }

    def __init__(self, state_tracker):
        self.state_tracker = state_tracker

    def can_resolve(self, reference_type: str) -> bool:
        return reference_type == "query"

    def resolve(self, reference: str, context: dict) -> str:
        """
        Resolve @query: reference.

        Examples:
            @query:stories.where(epic=3, status='done')
            @query:epics.where(status='active').format('json')
            @query:stories.where(epic={{epic}}).order_by('story_num')
        """
        # Parse query DSL
        query_ast = self._parse_query(reference)

        # Validate query
        self._validate_query(query_ast)

        # Build SQL
        sql = self._build_sql(query_ast)

        # Execute query
        results = self._execute_query(sql, query_ast['params'])

        # Format results
        return self._format_results(results, query_ast.get('format', 'markdown'))

    def _parse_query(self, query_str: str) -> Dict[str, Any]:
        """
        Parse query DSL into AST.

        Example:
            "stories.where(epic=3, status='done').format('markdown')"
            -> {
                'table': 'stories',
                'where': {'epic': 3, 'status': 'done'},
                'format': 'markdown'
            }
        """
        import re

        ast = {'params': {}}

        # Extract table
        table_match = re.match(r'^(\w+)\.', query_str)
        if not table_match:
            raise ValueError("Query must start with table name")
        ast['table'] = table_match.group(1)

        # Extract where clause
        where_match = re.search(r'where\(([^)]+)\)', query_str)
        if where_match:
            ast['where'] = self._parse_where(where_match.group(1))

        # Extract order_by
        order_match = re.search(r'order_by\([\'"](\w+)[\'"](?:,\s*[\'"](\w+)[\'"])?\)', query_str)
        if order_match:
            ast['order_by'] = order_match.group(1)
            ast['order_dir'] = order_match.group(2) or 'ASC'

        # Extract limit
        limit_match = re.search(r'limit\((\d+)\)', query_str)
        if limit_match:
            ast['limit'] = int(limit_match.group(1))

        # Extract format
        format_match = re.search(r'format\([\'"](\w+)[\'"]?\)', query_str)
        if format_match:
            ast['format'] = format_match.group(1)

        return ast

    def _parse_where(self, where_str: str) -> Dict[str, Any]:
        """Parse where clause into dict."""
        conditions = {}
        for condition in where_str.split(','):
            key, value = condition.split('=')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            # Try to convert to number
            try:
                value = int(value)
            except ValueError:
                pass
            conditions[key] = value
        return conditions

    def _validate_query(self, query_ast: Dict) -> None:
        """Validate query against whitelist."""
        table = query_ast['table']
        if table not in self.ALLOWED_TABLES:
            raise ValueError(f"Table not allowed: {table}")

        if 'where' in query_ast:
            for column in query_ast['where'].keys():
                if column not in self.ALLOWED_COLUMNS[table]:
                    raise ValueError(f"Column not allowed: {column}")

    def _build_sql(self, query_ast: Dict) -> str:
        """Build SQL from AST."""
        table = query_ast['table']
        sql = f"SELECT * FROM {table}"

        if 'where' in query_ast:
            conditions = []
            for key, value in query_ast['where'].items():
                conditions.append(f"{key} = :{key}")
            sql += " WHERE " + " AND ".join(conditions)

        if 'order_by' in query_ast:
            sql += f" ORDER BY {query_ast['order_by']} {query_ast.get('order_dir', 'ASC')}"

        if 'limit' in query_ast:
            sql += f" LIMIT {query_ast['limit']}"

        return sql

    def _execute_query(self, sql: str, params: Dict) -> List[Dict]:
        """Execute query with timeout."""
        return self.state_tracker.execute_query(sql, params, timeout=5)

    def _format_results(self, results: List[Dict], format_type: str) -> str:
        """Format query results."""
        if format_type == 'markdown':
            return self._format_markdown_table(results)
        elif format_type == 'json':
            return json.dumps(results, indent=2)
        elif format_type == 'csv':
            return self._format_csv(results)
        elif format_type == 'list':
            return self._format_list(results)
        else:
            raise ValueError(f"Unknown format: {format_type}")

    def _format_markdown_table(self, results: List[Dict]) -> str:
        """Format as markdown table."""
        if not results:
            return "*No results*"

        # Get headers
        headers = list(results[0].keys())

        # Build table
        lines = []
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        for row in results:
            lines.append("| " + " | ".join(str(row[h]) for h in headers) + " |")

        return "\n".join(lines)
```

### Query Examples

```yaml
# Get completed stories for epic
user_prompt: |
  Review the following completed stories:

  @query:stories.where(epic={{epic}}, status='done').format('markdown')

# Get epic progress
user_prompt: |
  Epic Progress:
  @query:epics.where(epic_num={{epic}}).format('json')

# Get blocked stories
user_prompt: |
  The following stories are blocked and need attention:

  @query:stories.where(status='blocked').order_by('priority').format('list')
```

**Files to Create:**
- `gao_dev/core/meta_prompts/resolvers/query_resolver.py`
- `gao_dev/core/meta_prompts/query_builder.py`
- `tests/core/meta_prompts/resolvers/test_query_resolver.py`

**Dependencies:**
- Story 13.1 (Reference Resolver Framework)
- Epic 15 (State Tracking Database)

---

## Testing Requirements

### Unit Tests

**Query Parsing:**
- [ ] Test parsing table name
- [ ] Test parsing where clause
- [ ] Test parsing order_by clause
- [ ] Test parsing limit clause
- [ ] Test parsing format option
- [ ] Test invalid query syntax

**Query Validation:**
- [ ] Test allowed tables accepted
- [ ] Test disallowed tables rejected
- [ ] Test allowed columns accepted
- [ ] Test disallowed columns rejected
- [ ] Test SQL injection attempts blocked

**Query Execution:**
- [ ] Test simple query
- [ ] Test query with filters
- [ ] Test query with ordering
- [ ] Test query with limit
- [ ] Test empty results
- [ ] Test query timeout

**Formatting:**
- [ ] Test markdown table format
- [ ] Test JSON format
- [ ] Test CSV format
- [ ] Test list format
- [ ] Test empty results formatting

### Integration Tests
- [ ] Test with real state database
- [ ] Test variable substitution ({{epic}})
- [ ] Test end-to-end in prompt template

### Performance Tests
- [ ] Query execution <100ms
- [ ] Result formatting <50ms
- [ ] Large result set (100 rows) <200ms

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Query syntax documentation
- [ ] Supported tables and columns reference
- [ ] Format options documentation
- [ ] Examples for common queries
- [ ] Security considerations documented

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Documentation complete
- [ ] No SQL injection vulnerabilities
- [ ] Performance benchmarks met
- [ ] Integrated with ReferenceResolverRegistry
- [ ] Committed with atomic commit message:
  ```
  feat(epic-13): implement Story 13.3 - Query Reference Resolver

  - Implement QueryResolver for @query: references
  - Add query DSL parser and validator
  - Support multiple output formats (markdown, json, csv, list)
  - Whitelist tables and columns for security
  - Prevent SQL injection with parameter binding
  - Add comprehensive tests (>80% coverage)

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
