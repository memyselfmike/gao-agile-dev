"""
Query reference resolver for @query: references.

This resolver executes database queries and injects results into prompts.
It supports:
- SQL-like query DSL (stories.where(epic=3, status='done'))
- Query validation with whitelist (tables, columns)
- Parameter binding for SQL injection prevention
- Multiple output formats (markdown, json, csv, list)
- Query timeouts and result limits
"""

import re
import json
import csv
import io
import signal
from typing import Dict, Any, List, Optional, Callable
from contextlib import contextmanager
import structlog

from gao_dev.core.meta_prompts.reference_resolver import ReferenceResolver

logger = structlog.get_logger(__name__)


class QueryTimeout(Exception):
    """Exception raised when query execution times out."""
    pass


class QueryResolver(ReferenceResolver):
    """
    Resolver for @query: references.

    This resolver executes database queries and formats results for prompt injection.
    It provides a SQL-like DSL with safety features:

    Query Syntax:
        @query:table.where(col=value).order_by('col').limit(10).format('markdown')

    Supported Tables:
        - stories: User stories and tasks
        - epics: Epic-level features
        - sprints: Sprint information
        - documents: Document metadata

    Examples:
        >>> resolver = QueryResolver(db_connection)
        >>>
        >>> # Get completed stories for epic
        >>> result = resolver.resolve(
        ...     "stories.where(epic=3, status='done')",
        ...     {}
        ... )
        >>>
        >>> # Get epic progress in JSON
        >>> result = resolver.resolve(
        ...     "epics.where(epic_num=5).format('json')",
        ...     {}
        ... )
        >>>
        >>> # Get blocked stories
        >>> result = resolver.resolve(
        ...     "stories.where(status='blocked').order_by('priority').format('list')",
        ...     {}
        ... )

    Args:
        query_executor: Callable that executes SQL queries with parameters
        max_result_chars: Maximum characters in result (default: 10000)
        query_timeout: Query timeout in seconds (default: 5)
    """

    # Whitelist of allowed tables
    ALLOWED_TABLES = {'stories', 'epics', 'sprints', 'documents'}

    # Whitelist of allowed columns per table
    ALLOWED_COLUMNS = {
        'stories': {
            'id', 'epic', 'epic_num', 'story_num', 'title', 'status',
            'priority', 'points', 'owner', 'created_at', 'updated_at'
        },
        'epics': {
            'id', 'epic_num', 'name', 'status', 'total_points',
            'completed_points', 'created_at', 'updated_at'
        },
        'sprints': {
            'id', 'sprint_num', 'name', 'status', 'start_date',
            'end_date', 'created_at'
        },
        'documents': {
            'id', 'path', 'type', 'state', 'author', 'owner',
            'created_at', 'updated_at'
        }
    }

    # Allowed format types
    ALLOWED_FORMATS = {'markdown', 'json', 'csv', 'list'}

    def __init__(
        self,
        query_executor: Callable[[str, Dict[str, Any]], List[Dict[str, Any]]],
        max_result_chars: int = 10000,
        query_timeout: int = 5
    ):
        """
        Initialize query resolver.

        Args:
            query_executor: Function that executes SQL queries
                Signature: (sql: str, params: dict) -> List[dict]
            max_result_chars: Maximum characters in formatted result
            query_timeout: Query timeout in seconds
        """
        self.query_executor = query_executor
        self.max_result_chars = max_result_chars
        self.query_timeout = query_timeout

    def can_resolve(self, reference_type: str) -> bool:
        """
        Check if this resolver can handle the reference type.

        Args:
            reference_type: Type of reference (e.g., "query", "doc")

        Returns:
            True if type is "query"
        """
        return reference_type == "query"

    def resolve(self, reference: str, context: Dict[str, Any]) -> str:
        """
        Resolve @query: reference to query results.

        Parses query DSL, validates against whitelist, executes query,
        and formats results.

        Args:
            reference: Query DSL string (e.g., "stories.where(epic=3)")
            context: Context dict with variables for substitution

        Returns:
            Formatted query results as string

        Raises:
            ValueError: If query syntax is invalid or security check fails
            QueryTimeout: If query execution exceeds timeout
        """
        logger.debug("resolving_query_reference", reference=reference)

        # Parse query DSL into AST
        try:
            query_ast = self._parse_query(reference, context)
        except Exception as e:
            logger.error("query_parse_error", reference=reference, error=str(e))
            raise ValueError(f"Invalid query syntax: {str(e)}")

        # Validate query against whitelist
        try:
            self._validate_query(query_ast)
        except Exception as e:
            logger.error("query_validation_error", query=query_ast, error=str(e))
            raise ValueError(f"Query validation failed: {str(e)}")

        # Build SQL from AST
        sql = self._build_sql(query_ast)
        params = query_ast.get('params', {})

        logger.debug("executing_query", sql=sql, params=params)

        # Execute query with timeout
        try:
            results = self._execute_query_with_timeout(sql, params)
        except QueryTimeout:
            logger.error("query_timeout", sql=sql, timeout=self.query_timeout)
            raise
        except Exception as e:
            logger.error("query_execution_error", sql=sql, error=str(e))
            raise ValueError(f"Query execution failed: {str(e)}")

        # Format results
        format_type = query_ast.get('format', 'markdown')
        try:
            formatted = self._format_results(results, format_type)
        except Exception as e:
            logger.error("result_formatting_error", format=format_type, error=str(e))
            raise ValueError(f"Result formatting failed: {str(e)}")

        # Enforce result size limit
        if len(formatted) > self.max_result_chars:
            logger.warning(
                "result_truncated",
                original_size=len(formatted),
                max_size=self.max_result_chars
            )
            formatted = formatted[:self.max_result_chars] + "\n...(truncated)"

        logger.info(
            "query_resolved",
            table=query_ast['table'],
            result_count=len(results),
            format=format_type
        )

        return formatted

    def _parse_query(self, query_str: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse query DSL into Abstract Syntax Tree (AST).

        Syntax:
            table.where(key=value, ...).order_by('col', 'dir').limit(n).format('type')

        Args:
            query_str: Query DSL string
            context: Context for variable substitution

        Returns:
            AST dict with keys: table, where, order_by, order_dir, limit, format, params

        Example:
            "stories.where(epic=3, status='done').order_by('story_num').limit(10)"
            -> {
                'table': 'stories',
                'where': {'epic': 3, 'status': 'done'},
                'order_by': 'story_num',
                'order_dir': 'ASC',
                'limit': 10,
                'format': 'markdown',
                'params': {}
            }
        """
        ast: Dict[str, Any] = {'params': {}}

        # Substitute context variables ({{var}})
        query_str = self._substitute_variables(query_str, context)

        # Extract table name
        table_match = re.match(r'^(\w+)(?:\.|$)', query_str)
        if not table_match:
            raise ValueError("Query must start with table name")
        ast['table'] = table_match.group(1)

        # Extract where clause
        where_match = re.search(r'\.where\(([^)]+)\)', query_str)
        if where_match:
            ast['where'] = self._parse_where(where_match.group(1))

        # Extract order_by clause
        order_match = re.search(
            r"\.order_by\(['\"](\w+)['\"](?:\s*,\s*['\"](\w+)['\"])?\)",
            query_str
        )
        if order_match:
            ast['order_by'] = order_match.group(1)
            ast['order_dir'] = (order_match.group(2) or 'ASC').upper()
            # Validate order direction
            if ast['order_dir'] not in ('ASC', 'DESC'):
                raise ValueError(f"Invalid order direction: {ast['order_dir']}")

        # Extract limit clause
        limit_match = re.search(r'\.limit\((\d+)\)', query_str)
        if limit_match:
            ast['limit'] = int(limit_match.group(1))
            if ast['limit'] <= 0:
                raise ValueError("Limit must be positive")
            if ast['limit'] > 1000:
                raise ValueError("Limit cannot exceed 1000")

        # Extract format clause
        format_match = re.search(r"\.format\(['\"](\w+)['\"]?\)", query_str)
        if format_match:
            ast['format'] = format_match.group(1)
        else:
            ast['format'] = 'markdown'  # Default format

        return ast

    def _substitute_variables(self, query_str: str, context: Dict[str, Any]) -> str:
        """
        Substitute context variables in query string.

        Replaces {{var}} with context['var'] value.

        Args:
            query_str: Query string with {{var}} placeholders
            context: Context dict with variable values

        Returns:
            Query string with variables substituted
        """
        def replace_var(match):
            var_name = match.group(1)
            if var_name not in context:
                logger.warning("variable_not_found", var=var_name)
                return match.group(0)  # Keep original if not found
            value = context[var_name]
            # Quote string values, keep numbers as-is
            if isinstance(value, str):
                return f"'{value}'"
            return str(value)

        return re.sub(r'\{\{(\w+)\}\}', replace_var, query_str)

    def _parse_where(self, where_str: str) -> Dict[str, Any]:
        """
        Parse where clause into dict.

        Supports:
            - key=value (numbers and strings)
            - Multiple conditions separated by commas

        Args:
            where_str: Where clause string (e.g., "epic=3, status='done'")

        Returns:
            Dict of column -> value mappings
        """
        conditions = {}

        # Manual parsing to handle commas correctly
        # Split by comma, but respect quoted strings
        parts = []
        current = []
        in_quotes = False
        quote_char = None

        for char in where_str:
            if char in ('"', "'") and (not in_quotes or char == quote_char):
                in_quotes = not in_quotes
                quote_char = char if in_quotes else None
                current.append(char)
            elif char == ',' and not in_quotes:
                parts.append(''.join(current).strip())
                current = []
            else:
                current.append(char)

        if current:
            parts.append(''.join(current).strip())

        for part in parts:
            # Match key=value
            match = re.match(r'(\w+)\s*=\s*(.+)', part)
            if not match:
                raise ValueError(f"Invalid where clause: {part}")

            key = match.group(1)
            value_str = match.group(2).strip()

            # Remove quotes if present
            if (value_str.startswith("'") and value_str.endswith("'")) or \
               (value_str.startswith('"') and value_str.endswith('"')):
                value = value_str[1:-1]
            else:
                # Try to convert to number
                try:
                    value = int(value_str)
                except ValueError:
                    try:
                        value = float(value_str)
                    except ValueError:
                        value = value_str

            conditions[key] = value

        return conditions

    def _validate_query(self, query_ast: Dict[str, Any]) -> None:
        """
        Validate query against security whitelist.

        Checks:
            - Table is in ALLOWED_TABLES
            - All columns are in ALLOWED_COLUMNS for the table
            - No SQL keywords that could indicate injection

        Args:
            query_ast: Parsed query AST

        Raises:
            ValueError: If validation fails
        """
        table = query_ast['table']

        # Check table whitelist
        if table not in self.ALLOWED_TABLES:
            raise ValueError(f"Table not allowed: {table}")

        # Check column whitelist for where clause
        if 'where' in query_ast:
            allowed_cols = self.ALLOWED_COLUMNS[table]
            for column in query_ast['where'].keys():
                if column not in allowed_cols:
                    raise ValueError(
                        f"Column '{column}' not allowed for table '{table}'"
                    )

        # Check column whitelist for order_by
        if 'order_by' in query_ast:
            allowed_cols = self.ALLOWED_COLUMNS[table]
            if query_ast['order_by'] not in allowed_cols:
                raise ValueError(
                    f"Column '{query_ast['order_by']}' not allowed for table '{table}'"
                )

        # Check format is valid
        format_type = query_ast.get('format', 'markdown')
        if format_type not in self.ALLOWED_FORMATS:
            raise ValueError(f"Format not allowed: {format_type}")

    def _build_sql(self, query_ast: Dict[str, Any]) -> str:
        """
        Build parameterized SQL from AST.

        Uses parameter binding (:{param}) to prevent SQL injection.

        Args:
            query_ast: Parsed query AST

        Returns:
            SQL string with parameter placeholders
        """
        table = query_ast['table']
        sql = f"SELECT * FROM {table}"

        # Add WHERE clause
        if 'where' in query_ast:
            conditions = []
            for key in query_ast['where'].keys():
                conditions.append(f"{key} = :{key}")
            sql += " WHERE " + " AND ".join(conditions)

            # Store params for binding
            query_ast['params'] = query_ast['where']

        # Add ORDER BY clause
        if 'order_by' in query_ast:
            sql += f" ORDER BY {query_ast['order_by']} {query_ast.get('order_dir', 'ASC')}"

        # Add LIMIT clause
        if 'limit' in query_ast:
            sql += f" LIMIT {query_ast['limit']}"

        return sql

    def _execute_query_with_timeout(
        self,
        sql: str,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Execute query with timeout.

        Uses signal alarm on Unix or threading timeout on Windows.

        Args:
            sql: SQL query string
            params: Query parameters for binding

        Returns:
            List of result rows as dicts

        Raises:
            QueryTimeout: If query exceeds timeout
        """
        import platform

        if platform.system() == 'Windows':
            # Windows doesn't support signal.alarm, use threading
            import threading

            result = []
            exception = []

            def target():
                try:
                    result.append(self.query_executor(sql, params))
                except Exception as e:
                    exception.append(e)

            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout=self.query_timeout)

            if thread.is_alive():
                # Timeout occurred
                raise QueryTimeout(
                    f"Query exceeded {self.query_timeout}s timeout"
                )

            if exception:
                raise exception[0]

            return result[0] if result else []
        else:
            # Unix: use signal.alarm
            def timeout_handler(signum, frame):
                raise QueryTimeout(
                    f"Query exceeded {self.query_timeout}s timeout"
                )

            # Set alarm
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.query_timeout)

            try:
                results = self.query_executor(sql, params)
            finally:
                # Cancel alarm
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

            return results

    def _format_results(
        self,
        results: List[Dict[str, Any]],
        format_type: str
    ) -> str:
        """
        Format query results for output.

        Args:
            results: List of result rows as dicts
            format_type: Output format (markdown, json, csv, list)

        Returns:
            Formatted string

        Raises:
            ValueError: If format_type is unknown
        """
        if format_type == 'markdown':
            return self._format_markdown_table(results)
        elif format_type == 'json':
            return self._format_json(results)
        elif format_type == 'csv':
            return self._format_csv(results)
        elif format_type == 'list':
            return self._format_list(results)
        else:
            raise ValueError(f"Unknown format: {format_type}")

    def _format_markdown_table(self, results: List[Dict[str, Any]]) -> str:
        """
        Format results as markdown table.

        Args:
            results: List of result rows

        Returns:
            Markdown table string
        """
        if not results:
            return "*No results*"

        # Get headers from first row
        headers = list(results[0].keys())

        # Build table
        lines = []
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        for row in results:
            values = [str(row.get(h, '')) for h in headers]
            lines.append("| " + " | ".join(values) + " |")

        return "\n".join(lines)

    def _format_json(self, results: List[Dict[str, Any]]) -> str:
        """
        Format results as JSON array.

        Args:
            results: List of result rows

        Returns:
            JSON string
        """
        return json.dumps(results, indent=2, default=str)

    def _format_csv(self, results: List[Dict[str, Any]]) -> str:
        """
        Format results as CSV.

        Args:
            results: List of result rows

        Returns:
            CSV string
        """
        if not results:
            return ""

        output = io.StringIO()
        headers = list(results[0].keys())
        writer = csv.DictWriter(output, fieldnames=headers)

        writer.writeheader()
        writer.writerows(results)

        return output.getvalue()

    def _format_list(self, results: List[Dict[str, Any]]) -> str:
        """
        Format results as bullet list.

        Each row is formatted as:
        - {first_col}: {remaining_cols}

        Args:
            results: List of result rows

        Returns:
            Bullet list string
        """
        if not results:
            return "*No results*"

        lines = []
        headers = list(results[0].keys())

        for row in results:
            # Use first column as main item
            main = str(row[headers[0]])

            # Add remaining columns as description
            if len(headers) > 1:
                details = ", ".join(
                    f"{k}={v}" for k, v in row.items()
                    if k != headers[0]
                )
                lines.append(f"- {main} ({details})")
            else:
                lines.append(f"- {main}")

        return "\n".join(lines)
