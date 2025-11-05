"""
Comprehensive unit tests for QueryResolver.

Tests all aspects of query reference resolution:
- Query DSL parsing
- Query validation and security
- SQL building with parameter binding
- Query execution with timeout
- Result formatting (markdown, json, csv, list)
- Variable substitution
- Error handling
- Performance characteristics
"""

import pytest
import time
from typing import List, Dict, Any
from unittest.mock import Mock, MagicMock

from gao_dev.core.meta_prompts.resolvers.query_resolver import (
    QueryResolver,
    QueryTimeout
)


class TestQueryResolverBasics:
    """Test basic QueryResolver functionality."""

    @pytest.fixture
    def mock_executor(self):
        """Create mock query executor."""
        def executor(sql: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
            # Simple mock that returns empty results
            return []
        return executor

    @pytest.fixture
    def resolver(self, mock_executor):
        """Create QueryResolver instance."""
        return QueryResolver(mock_executor)

    def test_can_resolve_query_type(self, resolver):
        """Test resolver identifies 'query' type."""
        assert resolver.can_resolve("query") is True
        assert resolver.can_resolve("doc") is False
        assert resolver.can_resolve("other") is False

    def test_get_type(self, resolver):
        """Test resolver returns correct type."""
        assert resolver.get_type() == "query"

    def test_allowed_tables_defined(self, resolver):
        """Test ALLOWED_TABLES is properly defined."""
        assert 'stories' in resolver.ALLOWED_TABLES
        assert 'epics' in resolver.ALLOWED_TABLES
        assert 'sprints' in resolver.ALLOWED_TABLES
        assert 'documents' in resolver.ALLOWED_TABLES

    def test_allowed_columns_defined(self, resolver):
        """Test ALLOWED_COLUMNS is properly defined for all tables."""
        for table in resolver.ALLOWED_TABLES:
            assert table in resolver.ALLOWED_COLUMNS
            assert len(resolver.ALLOWED_COLUMNS[table]) > 0


class TestQueryParsing:
    """Test query DSL parsing."""

    @pytest.fixture
    def resolver(self):
        """Create QueryResolver with mock executor."""
        mock_executor = Mock(return_value=[])
        return QueryResolver(mock_executor)

    def test_parse_simple_table_query(self, resolver):
        """Test parsing simple table query."""
        ast = resolver._parse_query("stories", {})

        assert ast['table'] == 'stories'
        assert ast['format'] == 'markdown'

    def test_parse_where_clause(self, resolver):
        """Test parsing where clause."""
        ast = resolver._parse_query("stories.where(epic=3, status='done')", {})

        assert ast['table'] == 'stories'
        assert ast['where'] == {'epic': 3, 'status': 'done'}

    def test_parse_where_with_string_values(self, resolver):
        """Test parsing where clause with quoted strings."""
        ast = resolver._parse_query("stories.where(status='in_progress')", {})

        assert ast['where'] == {'status': 'in_progress'}

    def test_parse_where_with_numeric_values(self, resolver):
        """Test parsing where clause with numbers."""
        ast = resolver._parse_query("stories.where(epic=5, points=8)", {})

        assert ast['where'] == {'epic': 5, 'points': 8}

    def test_parse_order_by_clause(self, resolver):
        """Test parsing order_by clause."""
        ast = resolver._parse_query("stories.order_by('story_num')", {})

        assert ast['order_by'] == 'story_num'
        assert ast['order_dir'] == 'ASC'

    def test_parse_order_by_with_direction(self, resolver):
        """Test parsing order_by with explicit direction."""
        ast = resolver._parse_query("stories.order_by('priority', 'DESC')", {})

        assert ast['order_by'] == 'priority'
        assert ast['order_dir'] == 'DESC'

    def test_parse_limit_clause(self, resolver):
        """Test parsing limit clause."""
        ast = resolver._parse_query("stories.limit(10)", {})

        assert ast['limit'] == 10

    def test_parse_format_clause(self, resolver):
        """Test parsing format clause."""
        ast = resolver._parse_query("stories.format('json')", {})

        assert ast['format'] == 'json'

    def test_parse_complex_query(self, resolver):
        """Test parsing query with all clauses."""
        query = "stories.where(epic=3).order_by('story_num', 'ASC').limit(5).format('csv')"
        ast = resolver._parse_query(query, {})

        assert ast['table'] == 'stories'
        assert ast['where'] == {'epic': 3}
        assert ast['order_by'] == 'story_num'
        assert ast['order_dir'] == 'ASC'
        assert ast['limit'] == 5
        assert ast['format'] == 'csv'

    def test_parse_missing_table_raises_error(self, resolver):
        """Test query without table name raises error."""
        with pytest.raises(ValueError, match="must start with table name"):
            resolver._parse_query(".where(epic=3)", {})

    def test_parse_invalid_order_direction(self, resolver):
        """Test invalid order direction raises error."""
        with pytest.raises(ValueError, match="Invalid order direction"):
            resolver._parse_query("stories.order_by('id', 'INVALID')", {})

    def test_parse_zero_limit_raises_error(self, resolver):
        """Test zero limit raises error."""
        with pytest.raises(ValueError, match="Limit must be positive"):
            resolver._parse_query("stories.limit(0)", {})

    def test_parse_excessive_limit_raises_error(self, resolver):
        """Test excessive limit raises error."""
        with pytest.raises(ValueError, match="cannot exceed 1000"):
            resolver._parse_query("stories.limit(9999)", {})


class TestVariableSubstitution:
    """Test variable substitution in queries."""

    @pytest.fixture
    def resolver(self):
        """Create QueryResolver with mock executor."""
        mock_executor = Mock(return_value=[])
        return QueryResolver(mock_executor)

    def test_substitute_numeric_variable(self, resolver):
        """Test numeric variable substitution."""
        ast = resolver._parse_query("stories.where(epic={{epic_num}})", {'epic_num': 5})

        assert ast['where'] == {'epic': 5}

    def test_substitute_string_variable(self, resolver):
        """Test string variable substitution."""
        ast = resolver._parse_query(
            "stories.where(status={{status}})",
            {'status': 'done'}
        )

        assert ast['where'] == {'status': 'done'}

    def test_substitute_multiple_variables(self, resolver):
        """Test multiple variable substitution."""
        context = {'epic_num': 3, 'status': 'active'}
        ast = resolver._parse_query(
            "stories.where(epic={{epic_num}}, status={{status}})",
            context
        )

        assert ast['where'] == {'epic': 3, 'status': 'active'}

    def test_missing_variable_keeps_placeholder(self, resolver):
        """Test missing variable keeps original placeholder."""
        result = resolver._substitute_variables("epic={{missing}}", {})

        assert "{{missing}}" in result


class TestQueryValidation:
    """Test query validation and security."""

    @pytest.fixture
    def resolver(self):
        """Create QueryResolver with mock executor."""
        mock_executor = Mock(return_value=[])
        return QueryResolver(mock_executor)

    def test_validate_allowed_table(self, resolver):
        """Test allowed table passes validation."""
        ast = {'table': 'stories', 'format': 'markdown'}

        # Should not raise
        resolver._validate_query(ast)

    def test_validate_disallowed_table_raises_error(self, resolver):
        """Test disallowed table raises error."""
        ast = {'table': 'users', 'format': 'markdown'}

        with pytest.raises(ValueError, match="Table not allowed"):
            resolver._validate_query(ast)

    def test_validate_allowed_columns(self, resolver):
        """Test allowed columns pass validation."""
        ast = {
            'table': 'stories',
            'where': {'epic_num': 3, 'status': 'done'},
            'format': 'markdown'
        }

        # Should not raise
        resolver._validate_query(ast)

    def test_validate_disallowed_column_raises_error(self, resolver):
        """Test disallowed column raises error."""
        ast = {
            'table': 'stories',
            'where': {'password': 'secret'},  # Not in whitelist
            'format': 'markdown'
        }

        with pytest.raises(ValueError, match="Column .* not allowed"):
            resolver._validate_query(ast)

    def test_validate_order_by_column(self, resolver):
        """Test order_by column validation."""
        ast = {
            'table': 'stories',
            'order_by': 'story_num',
            'format': 'markdown'
        }

        # Should not raise
        resolver._validate_query(ast)

    def test_validate_order_by_disallowed_column(self, resolver):
        """Test order_by with disallowed column raises error."""
        ast = {
            'table': 'stories',
            'order_by': 'secret_field',
            'format': 'markdown'
        }

        with pytest.raises(ValueError, match="Column .* not allowed"):
            resolver._validate_query(ast)

    def test_validate_allowed_format(self, resolver):
        """Test allowed format passes validation."""
        for fmt in ['markdown', 'json', 'csv', 'list']:
            ast = {'table': 'stories', 'format': fmt}
            resolver._validate_query(ast)

    def test_validate_disallowed_format_raises_error(self, resolver):
        """Test disallowed format raises error."""
        ast = {'table': 'stories', 'format': 'xml'}

        with pytest.raises(ValueError, match="Format not allowed"):
            resolver._validate_query(ast)


class TestSQLBuilding:
    """Test SQL building with parameter binding."""

    @pytest.fixture
    def resolver(self):
        """Create QueryResolver with mock executor."""
        mock_executor = Mock(return_value=[])
        return QueryResolver(mock_executor)

    def test_build_simple_select(self, resolver):
        """Test building simple SELECT query."""
        ast = {'table': 'stories', 'params': {}}
        sql = resolver._build_sql(ast)

        assert sql == "SELECT * FROM stories"

    def test_build_with_where_clause(self, resolver):
        """Test building query with WHERE clause."""
        ast = {
            'table': 'stories',
            'where': {'epic': 3, 'status': 'done'},
            'params': {}
        }
        sql = resolver._build_sql(ast)

        assert "SELECT * FROM stories" in sql
        assert "WHERE" in sql
        assert "epic = :epic" in sql
        assert "status = :status" in sql
        # Params should be stored
        assert ast['params'] == {'epic': 3, 'status': 'done'}

    def test_build_with_order_by(self, resolver):
        """Test building query with ORDER BY."""
        ast = {
            'table': 'stories',
            'order_by': 'story_num',
            'order_dir': 'ASC',
            'params': {}
        }
        sql = resolver._build_sql(ast)

        assert "ORDER BY story_num ASC" in sql

    def test_build_with_limit(self, resolver):
        """Test building query with LIMIT."""
        ast = {'table': 'stories', 'limit': 10, 'params': {}}
        sql = resolver._build_sql(ast)

        assert "LIMIT 10" in sql

    def test_build_complex_query(self, resolver):
        """Test building complex query with all clauses."""
        ast = {
            'table': 'stories',
            'where': {'epic': 5},
            'order_by': 'priority',
            'order_dir': 'DESC',
            'limit': 20,
            'params': {}
        }
        sql = resolver._build_sql(ast)

        assert "SELECT * FROM stories" in sql
        assert "WHERE epic = :epic" in sql
        assert "ORDER BY priority DESC" in sql
        assert "LIMIT 20" in sql

    def test_parameter_binding_prevents_injection(self, resolver):
        """Test parameter binding uses placeholders."""
        ast = {
            'table': 'stories',
            'where': {'status': "'; DROP TABLE stories; --"},
            'params': {}
        }
        sql = resolver._build_sql(ast)

        # SQL should use parameter placeholder, not inline value
        assert ":status" in sql
        assert "DROP TABLE" not in sql


class TestQueryExecution:
    """Test query execution."""

    def test_execute_simple_query(self):
        """Test executing simple query."""
        expected_results = [
            {'id': 1, 'title': 'Story 1'},
            {'id': 2, 'title': 'Story 2'}
        ]

        mock_executor = Mock(return_value=expected_results)
        resolver = QueryResolver(mock_executor)

        results = resolver._execute_query_with_timeout(
            "SELECT * FROM stories",
            {}
        )

        assert results == expected_results
        mock_executor.assert_called_once_with("SELECT * FROM stories", {})

    def test_execute_with_parameters(self):
        """Test executing query with parameters."""
        expected_results = [{'id': 1, 'epic': 3}]
        mock_executor = Mock(return_value=expected_results)
        resolver = QueryResolver(mock_executor)

        results = resolver._execute_query_with_timeout(
            "SELECT * FROM stories WHERE epic = :epic",
            {'epic': 3}
        )

        assert results == expected_results
        mock_executor.assert_called_once()

    def test_query_timeout_raises_exception(self):
        """Test query timeout raises QueryTimeout."""
        def slow_executor(sql, params):
            time.sleep(10)  # Sleep longer than timeout
            return []

        resolver = QueryResolver(slow_executor, query_timeout=1)

        with pytest.raises(QueryTimeout):
            resolver._execute_query_with_timeout("SELECT * FROM stories", {})

    def test_query_execution_error_propagates(self):
        """Test query execution error is propagated."""
        def failing_executor(sql, params):
            raise RuntimeError("Database error")

        resolver = QueryResolver(failing_executor)

        with pytest.raises(RuntimeError, match="Database error"):
            resolver._execute_query_with_timeout("SELECT * FROM stories", {})


class TestResultFormatting:
    """Test result formatting in various formats."""

    @pytest.fixture
    def sample_results(self):
        """Create sample query results."""
        return [
            {'id': 1, 'title': 'Story 1', 'status': 'done'},
            {'id': 2, 'title': 'Story 2', 'status': 'in_progress'},
            {'id': 3, 'title': 'Story 3', 'status': 'pending'}
        ]

    @pytest.fixture
    def resolver(self):
        """Create QueryResolver with mock executor."""
        mock_executor = Mock(return_value=[])
        return QueryResolver(mock_executor)

    def test_format_markdown_table(self, resolver, sample_results):
        """Test formatting as markdown table."""
        result = resolver._format_markdown_table(sample_results)

        assert "| id | title | status |" in result
        assert "| --- | --- | --- |" in result
        assert "| 1 | Story 1 | done |" in result
        assert "| 2 | Story 2 | in_progress |" in result

    def test_format_markdown_empty_results(self, resolver):
        """Test formatting empty results as markdown."""
        result = resolver._format_markdown_table([])

        assert result == "*No results*"

    def test_format_json(self, resolver, sample_results):
        """Test formatting as JSON."""
        result = resolver._format_json(sample_results)

        assert '"id": 1' in result
        assert '"title": "Story 1"' in result
        assert '"status": "done"' in result

    def test_format_json_empty_results(self, resolver):
        """Test formatting empty results as JSON."""
        result = resolver._format_json([])

        assert result == "[]"

    def test_format_csv(self, resolver, sample_results):
        """Test formatting as CSV."""
        result = resolver._format_csv(sample_results)

        lines = result.strip().split('\n')
        assert "id,title,status" in lines[0]
        assert "1,Story 1,done" in lines[1]
        assert "2,Story 2,in_progress" in lines[2]

    def test_format_csv_empty_results(self, resolver):
        """Test formatting empty results as CSV."""
        result = resolver._format_csv([])

        assert result == ""

    def test_format_list(self, resolver, sample_results):
        """Test formatting as bullet list."""
        result = resolver._format_list(sample_results)

        assert "- 1 (title=Story 1, status=done)" in result
        assert "- 2 (title=Story 2, status=in_progress)" in result
        assert "- 3 (title=Story 3, status=pending)" in result

    def test_format_list_empty_results(self, resolver):
        """Test formatting empty results as list."""
        result = resolver._format_list([])

        assert result == "*No results*"

    def test_format_list_single_column(self, resolver):
        """Test formatting list with single column."""
        results = [{'title': 'Story 1'}, {'title': 'Story 2'}]
        result = resolver._format_list(results)

        assert "- Story 1" in result
        assert "- Story 2" in result
        assert "(" not in result  # No details for single column

    def test_format_unknown_type_raises_error(self, resolver, sample_results):
        """Test unknown format type raises error."""
        with pytest.raises(ValueError, match="Unknown format"):
            resolver._format_results(sample_results, 'xml')


class TestEndToEndResolution:
    """Test end-to-end query resolution."""

    def test_resolve_simple_query(self):
        """Test resolving simple query."""
        results = [
            {'id': 1, 'title': 'Story 1', 'status': 'done'},
            {'id': 2, 'title': 'Story 2', 'status': 'done'}
        ]

        mock_executor = Mock(return_value=results)
        resolver = QueryResolver(mock_executor)

        output = resolver.resolve("stories.where(status='done')", {})

        # Should be markdown table by default
        assert "| id | title | status |" in output
        assert "Story 1" in output
        assert "Story 2" in output

    def test_resolve_with_json_format(self):
        """Test resolving query with JSON format."""
        results = [{'id': 1, 'title': 'Story 1'}]

        mock_executor = Mock(return_value=results)
        resolver = QueryResolver(mock_executor)

        output = resolver.resolve("stories.format('json')", {})

        assert '"id": 1' in output
        assert '"title": "Story 1"' in output

    def test_resolve_with_variable_substitution(self):
        """Test resolving query with variable substitution."""
        results = [{'id': 1, 'epic': 5}]

        mock_executor = Mock(return_value=results)
        resolver = QueryResolver(mock_executor)

        output = resolver.resolve(
            "stories.where(epic={{epic_num}})",
            {'epic_num': 5}
        )

        # Verify executor called with correct params
        mock_executor.assert_called_once()
        call_args = mock_executor.call_args
        assert call_args[0][1] == {'epic': 5}

    def test_resolve_complex_query(self):
        """Test resolving complex query with all features."""
        results = [
            {'id': 1, 'title': 'High Priority', 'priority': 'P0'},
            {'id': 2, 'title': 'Medium Priority', 'priority': 'P1'}
        ]

        mock_executor = Mock(return_value=results)
        resolver = QueryResolver(mock_executor)

        output = resolver.resolve(
            "stories.where(epic=3).order_by('priority').limit(10).format('list')",
            {}
        )

        assert "- 1" in output
        assert "High Priority" in output

    def test_resolve_invalid_query_raises_error(self):
        """Test resolving invalid query raises error."""
        mock_executor = Mock(return_value=[])
        resolver = QueryResolver(mock_executor)

        with pytest.raises(ValueError):
            resolver.resolve(".where(epic=3)", {})  # Missing table

    def test_resolve_injection_attempt_blocked(self):
        """Test SQL injection attempt is blocked."""
        mock_executor = Mock(return_value=[])
        resolver = QueryResolver(mock_executor)

        with pytest.raises(ValueError, match="not allowed"):
            resolver.resolve(
                "users.where(password='secret')",  # 'users' not in whitelist
                {}
            )

    def test_resolve_with_result_size_limit(self):
        """Test result is truncated when exceeding max size."""
        # Create large result
        results = [{'id': i, 'title': 'X' * 1000} for i in range(100)]

        mock_executor = Mock(return_value=results)
        resolver = QueryResolver(mock_executor, max_result_chars=500)

        output = resolver.resolve("stories", {})

        assert len(output) <= 520  # 500 + truncation message
        assert "(truncated)" in output


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_empty_query_raises_error(self):
        """Test empty query raises error."""
        mock_executor = Mock(return_value=[])
        resolver = QueryResolver(mock_executor)

        with pytest.raises(ValueError):
            resolver.resolve("", {})

    def test_malformed_where_clause(self):
        """Test malformed where clause raises error."""
        mock_executor = Mock(return_value=[])
        resolver = QueryResolver(mock_executor)

        with pytest.raises(ValueError):
            resolver.resolve("stories.where(invalid)", {})

    def test_query_executor_exception_handled(self):
        """Test query executor exception is handled."""
        def failing_executor(sql, params):
            raise RuntimeError("Database connection failed")

        resolver = QueryResolver(failing_executor)

        with pytest.raises(ValueError, match="Query execution failed"):
            resolver.resolve("stories", {})

    def test_formatting_error_handled(self):
        """Test formatting error is handled gracefully."""
        # Mock executor that returns malformed data
        mock_executor = Mock(return_value=[None, None])
        resolver = QueryResolver(mock_executor)

        # Should handle gracefully
        with pytest.raises(ValueError, match="Result formatting failed"):
            resolver.resolve("stories", {})


class TestPerformance:
    """Test performance characteristics."""

    def test_parse_performance(self):
        """Test query parsing in <10ms."""
        mock_executor = Mock(return_value=[])
        resolver = QueryResolver(mock_executor)

        query = "stories.where(epic=3, status='done').order_by('id').limit(10)"

        start = time.perf_counter()
        for _ in range(100):
            resolver._parse_query(query, {})
        duration = (time.perf_counter() - start) / 100 * 1000  # ms per iteration

        assert duration < 10, f"Parse took {duration:.2f}ms, expected <10ms"

    def test_format_markdown_performance(self):
        """Test markdown formatting in <50ms for 100 rows."""
        results = [
            {'id': i, 'title': f'Story {i}', 'status': 'done'}
            for i in range(100)
        ]

        mock_executor = Mock(return_value=results)
        resolver = QueryResolver(mock_executor)

        start = time.perf_counter()
        resolver._format_markdown_table(results)
        duration = (time.perf_counter() - start) * 1000

        assert duration < 50, f"Format took {duration:.2f}ms, expected <50ms"

    def test_end_to_end_performance(self):
        """Test end-to-end resolution in <100ms."""
        results = [
            {'id': i, 'title': f'Story {i}', 'status': 'done'}
            for i in range(50)
        ]

        mock_executor = Mock(return_value=results)
        resolver = QueryResolver(mock_executor)

        start = time.perf_counter()
        resolver.resolve("stories.where(status='done')", {})
        duration = (time.perf_counter() - start) * 1000

        # Note: May vary based on system
        assert duration < 100, f"Resolve took {duration:.2f}ms, expected <100ms"


class TestIntegration:
    """Integration tests with realistic scenarios."""

    def test_epic_progress_query(self):
        """Test realistic epic progress query."""
        results = [
            {
                'epic_num': 13,
                'name': 'Meta-Prompt System',
                'status': 'in_progress',
                'total_points': 20,
                'completed_points': 8
            }
        ]

        mock_executor = Mock(return_value=results)
        resolver = QueryResolver(mock_executor)

        output = resolver.resolve(
            "epics.where(epic_num=13).format('json')",
            {}
        )

        assert '"epic_num": 13' in output
        assert '"name": "Meta-Prompt System"' in output

    def test_blocked_stories_query(self):
        """Test realistic blocked stories query."""
        results = [
            {'id': 1, 'title': 'Story 1', 'status': 'blocked', 'priority': 'P0'},
            {'id': 2, 'title': 'Story 2', 'status': 'blocked', 'priority': 'P1'}
        ]

        mock_executor = Mock(return_value=results)
        resolver = QueryResolver(mock_executor)

        output = resolver.resolve(
            "stories.where(status='blocked').order_by('priority').format('list')",
            {}
        )

        assert "Story 1" in output
        assert "Story 2" in output
        assert "blocked" in output

    def test_sprint_velocity_query(self):
        """Test realistic sprint velocity query."""
        results = [
            {
                'sprint_num': 5,
                'name': 'Sprint 5',
                'status': 'completed',
                'start_date': '2025-01-01',
                'end_date': '2025-01-14'
            }
        ]

        mock_executor = Mock(return_value=results)
        resolver = QueryResolver(mock_executor)

        output = resolver.resolve(
            "sprints.where(sprint_num=5).format('markdown')",
            {}
        )

        assert "Sprint 5" in output
        assert "completed" in output

    def test_document_lifecycle_query(self):
        """Test realistic document lifecycle query."""
        results = [
            {'path': 'docs/PRD.md', 'type': 'prd', 'state': 'active', 'owner': 'john'},
            {'path': 'docs/ARCH.md', 'type': 'architecture', 'state': 'active', 'owner': 'winston'}
        ]

        mock_executor = Mock(return_value=results)
        resolver = QueryResolver(mock_executor)

        output = resolver.resolve(
            "documents.where(state='active').format('csv')",
            {}
        )

        assert "PRD.md" in output
        assert "ARCH.md" in output
        assert "john" in output
