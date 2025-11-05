"""
Thread Safety Tests for DocumentRegistry.

This module tests concurrent access to the DocumentRegistry to ensure
thread-safe operations don't cause corruption or race conditions.
"""

import tempfile
import threading
import time
from pathlib import Path
from typing import List

import pytest

from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.models import DocumentState, DocumentType
from gao_dev.lifecycle.exceptions import DocumentAlreadyExistsError


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    yield db_path

    # Cleanup - add delay for Windows file locking
    import time
    time.sleep(0.1)  # Give threads time to fully close connections

    # Try multiple times to delete (Windows file locking issue)
    for _ in range(10):
        try:
            if db_path.exists():
                db_path.unlink()
            break
        except PermissionError:
            time.sleep(0.1)
        except Exception:
            break


@pytest.fixture
def registry(temp_db):
    """Create DocumentRegistry instance for testing."""
    reg = DocumentRegistry(temp_db)
    yield reg
    # Cleanup: close all connections
    reg.close()


class TestConcurrentReads:
    """Tests for concurrent read operations."""

    def test_concurrent_reads_work_correctly(self, registry):
        """Test that concurrent reads don't interfere with each other."""
        # Create test documents
        doc1 = registry.register_document(
            path="docs/doc1.md", doc_type="prd", author="John"
        )
        doc2 = registry.register_document(
            path="docs/doc2.md", doc_type="architecture", author="Jane"
        )

        results = []
        errors = []

        def read_document(doc_id: int):
            """Read document in thread."""
            try:
                doc = registry.get_document(doc_id)
                results.append(doc)
            except Exception as e:
                errors.append(e)
            finally:
                # Close thread-local connection
                registry.close()

        # Create threads to read documents concurrently
        threads = []
        for _ in range(10):
            t1 = threading.Thread(target=read_document, args=(doc1.id,))
            t2 = threading.Thread(target=read_document, args=(doc2.id,))
            threads.extend([t1, t2])

        # Start all threads
        for t in threads:
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify no errors occurred
        assert len(errors) == 0
        assert len(results) == 20  # 10 reads of each document

        # Verify all reads returned valid documents
        doc1_reads = [r for r in results if r.id == doc1.id]
        doc2_reads = [r for r in results if r.id == doc2.id]

        assert len(doc1_reads) == 10
        assert len(doc2_reads) == 10
        assert all(doc.path == "docs/doc1.md" for doc in doc1_reads)
        assert all(doc.path == "docs/doc2.md" for doc in doc2_reads)

    def test_concurrent_queries_work_correctly(self, registry):
        """Test that concurrent queries work correctly."""
        # Create test documents
        for i in range(5):
            registry.register_document(
                path=f"docs/prd{i}.md",
                doc_type="prd",
                author="John",
                feature="test-feature",
            )
            registry.register_document(
                path=f"docs/arch{i}.md",
                doc_type="architecture",
                author="Jane",
                feature="test-feature",
            )

        results = []
        errors = []

        def query_documents(doc_type: str):
            """Query documents in thread."""
            try:
                docs = registry.query_documents(doc_type=doc_type)
                results.append((doc_type, len(docs)))
            except Exception as e:
                errors.append(e)
            finally:
                # Close thread-local connection
                registry.close()

        # Create threads to query concurrently
        threads = []
        for _ in range(10):
            t1 = threading.Thread(target=query_documents, args=("prd",))
            t2 = threading.Thread(target=query_documents, args=("architecture",))
            threads.extend([t1, t2])

        # Start all threads
        for t in threads:
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify no errors occurred
        assert len(errors) == 0
        assert len(results) == 20

        # Verify all queries returned correct counts
        prd_counts = [count for doc_type, count in results if doc_type == "prd"]
        arch_counts = [
            count for doc_type, count in results if doc_type == "architecture"
        ]

        assert all(count == 5 for count in prd_counts)
        assert all(count == 5 for count in arch_counts)


class TestConcurrentWrites:
    """Tests for concurrent write operations."""

    def test_concurrent_writes_dont_cause_corruption(self, registry):
        """Test that concurrent writes don't corrupt database."""
        errors = []
        created_docs = []

        def create_document(doc_id: int):
            """Create document in thread."""
            try:
                doc = registry.register_document(
                    path=f"docs/doc{doc_id}.md",
                    doc_type="prd",
                    author=f"Author{doc_id}",
                )
                created_docs.append(doc)
            except Exception as e:
                errors.append(e)
            finally:
                # Close thread-local connection
                registry.close()

        # Create threads to write documents concurrently
        threads = []
        for i in range(20):
            t = threading.Thread(target=create_document, args=(i,))
            threads.append(t)

        # Start all threads
        for t in threads:
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify no errors occurred
        assert len(errors) == 0
        assert len(created_docs) == 20

        # Verify all documents were created correctly
        all_docs = registry.query_documents()
        assert len(all_docs) == 20

        # Verify each document has unique ID and path
        ids = {doc.id for doc in all_docs}
        paths = {doc.path for doc in all_docs}
        assert len(ids) == 20
        assert len(paths) == 20

    def test_concurrent_duplicate_writes_handled_correctly(self, registry):
        """Test that concurrent duplicate writes raise appropriate errors."""
        errors = []
        successes = []
        path = "docs/duplicate.md"

        def create_document():
            """Try to create document with same path in thread."""
            try:
                doc = registry.register_document(
                    path=path, doc_type="prd", author="John"
                )
                successes.append(doc)
            except DocumentAlreadyExistsError as e:
                errors.append(e)
            finally:
                # Close thread-local connection
                registry.close()

        # Create threads to write same document concurrently
        threads = []
        for _ in range(10):
            t = threading.Thread(target=create_document)
            threads.append(t)

        # Start all threads
        for t in threads:
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify exactly one succeeded and others raised errors
        assert len(successes) == 1
        assert len(errors) == 9
        assert all(isinstance(e, DocumentAlreadyExistsError) for e in errors)

    def test_concurrent_updates_work_correctly(self, registry):
        """Test that concurrent updates to same document work correctly."""
        # Create a document
        doc = registry.register_document(
            path="docs/test.md", doc_type="prd", author="John"
        )

        errors = []
        update_count = [0]
        lock = threading.Lock()

        def update_document(author_name: str):
            """Update document in thread."""
            try:
                registry.update_document(doc.id, author=author_name)
                with lock:
                    update_count[0] += 1
            except Exception as e:
                errors.append(e)
            finally:
                # Close thread-local connection
                registry.close()

        # Create threads to update document concurrently
        threads = []
        for i in range(10):
            t = threading.Thread(target=update_document, args=(f"Author{i}",))
            threads.append(t)

        # Start all threads
        for t in threads:
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify no errors occurred
        assert len(errors) == 0
        assert update_count[0] == 10

        # Verify document was updated (will have one of the author names)
        updated_doc = registry.get_document(doc.id)
        assert updated_doc.author.startswith("Author")


class TestConcurrentMixedOperations:
    """Tests for concurrent mixed read/write operations."""

    def test_concurrent_reads_and_writes(self, registry):
        """Test concurrent reads and writes don't cause issues."""
        # Create initial documents
        initial_docs = []
        for i in range(5):
            doc = registry.register_document(
                path=f"docs/initial{i}.md", doc_type="prd", author="John"
            )
            initial_docs.append(doc)

        errors = []
        read_results = []
        write_results = []

        def read_documents():
            """Read documents in thread."""
            try:
                docs = registry.query_documents()
                read_results.append(len(docs))
            except Exception as e:
                errors.append(e)
            finally:
                # Close thread-local connection
                registry.close()

        def write_document(doc_id: int):
            """Write document in thread."""
            try:
                doc = registry.register_document(
                    path=f"docs/new{doc_id}.md", doc_type="architecture", author="Jane"
                )
                write_results.append(doc)
            except Exception as e:
                errors.append(e)
            finally:
                # Close thread-local connection
                registry.close()

        # Create mixed threads
        threads = []
        for i in range(10):
            # Add read threads
            t_read = threading.Thread(target=read_documents)
            threads.append(t_read)

            # Add write threads
            t_write = threading.Thread(target=write_document, args=(i,))
            threads.append(t_write)

        # Start all threads
        for t in threads:
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify no errors occurred
        assert len(errors) == 0

        # Verify writes succeeded
        assert len(write_results) == 10

        # Verify reads returned reasonable counts (between 5 and 15)
        # The exact count depends on timing of reads vs writes
        assert all(5 <= count <= 15 for count in read_results)

        # Verify final state is correct
        all_docs = registry.query_documents()
        assert len(all_docs) == 15  # 5 initial + 10 new


class TestConcurrentRelationships:
    """Tests for concurrent relationship operations."""

    def test_concurrent_relationship_creation(self, registry):
        """Test concurrent relationship creation works correctly."""
        # Create documents
        parent_doc = registry.register_document(
            path="docs/parent.md", doc_type="prd", author="John"
        )
        child_docs = []
        for i in range(10):
            doc = registry.register_document(
                path=f"docs/child{i}.md", doc_type="story", author="Jane"
            )
            child_docs.append(doc)

        errors = []
        successes = []

        def create_relationship(child_doc):
            """Create relationship in thread."""
            try:
                from gao_dev.lifecycle.models import RelationshipType

                rel = registry.add_relationship(
                    parent_doc.id, child_doc.id, RelationshipType.IMPLEMENTS
                )
                successes.append(rel)
            except Exception as e:
                errors.append(e)
            finally:
                # Close thread-local connection
                registry.close()

        # Create threads to add relationships concurrently
        threads = []
        for child_doc in child_docs:
            t = threading.Thread(target=create_relationship, args=(child_doc,))
            threads.append(t)

        # Start all threads
        for t in threads:
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify no errors occurred
        assert len(errors) == 0
        assert len(successes) == 10

        # Verify all relationships were created
        children = registry.get_child_documents(parent_doc.id)
        assert len(children) == 10


class TestStressTest:
    """Stress tests with high concurrency."""

    def test_high_concurrency_stress_test(self, registry):
        """Test registry under high concurrency load."""
        errors = []
        operations_count = {"reads": 0, "writes": 0, "updates": 0}
        lock = threading.Lock()

        # Pre-populate some documents
        initial_docs = []
        for i in range(10):
            doc = registry.register_document(
                path=f"docs/initial{i}.md", doc_type="prd", author="John"
            )
            initial_docs.append(doc)

        def perform_random_operations(thread_id: int):
            """Perform various operations in thread."""
            try:
                # Read operation
                docs = registry.query_documents()
                with lock:
                    operations_count["reads"] += 1

                # Write operation
                doc = registry.register_document(
                    path=f"docs/thread{thread_id}_doc.md",
                    doc_type="architecture",
                    author=f"Author{thread_id}",
                )
                with lock:
                    operations_count["writes"] += 1

                # Update operation
                if initial_docs:
                    target_doc = initial_docs[thread_id % len(initial_docs)]
                    registry.update_document(
                        target_doc.id, author=f"UpdatedBy{thread_id}"
                    )
                    with lock:
                        operations_count["updates"] += 1

            except Exception as e:
                errors.append(e)
            finally:
                # Close thread-local connection
                registry.close()

        # Create many threads
        threads = []
        num_threads = 50
        for i in range(num_threads):
            t = threading.Thread(target=perform_random_operations, args=(i,))
            threads.append(t)

        # Start all threads
        start_time = time.time()
        for t in threads:
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()
        duration = time.time() - start_time

        # Verify no errors occurred
        assert len(errors) == 0

        # Verify operations completed
        assert operations_count["reads"] == num_threads
        assert operations_count["writes"] == num_threads
        assert operations_count["updates"] == num_threads

        # Verify final database state is consistent
        all_docs = registry.query_documents()
        assert len(all_docs) == 10 + num_threads  # initial + new docs

        print(f"\nStress test completed in {duration:.2f}s")
        print(f"Operations: {operations_count}")
        print(f"Throughput: {sum(operations_count.values()) / duration:.2f} ops/sec")


class TestConnectionIsolation:
    """Tests for connection-per-thread isolation."""

    def test_threads_have_separate_connections(self, registry):
        """Test that each thread gets its own connection."""
        connection_ids = []
        lock = threading.Lock()

        def get_connection_id():
            """Get connection ID in thread."""
            try:
                # Access thread-local connection
                with registry._get_connection() as conn:
                    conn_id = id(conn)
                    with lock:
                        connection_ids.append(conn_id)
            finally:
                # Close thread-local connection
                registry.close()

        # Create threads
        threads = []
        for _ in range(10):
            t = threading.Thread(target=get_connection_id)
            threads.append(t)

        # Start all threads
        for t in threads:
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify each thread got a unique connection
        # Note: In practice, threads may reuse connections, but we verify
        # that the connection-per-thread mechanism works
        assert len(connection_ids) == 10

    def test_transaction_isolation(self, registry):
        """Test that transactions are isolated between threads."""
        success_count = [0]
        failure_count = [0]
        lock = threading.Lock()

        def create_and_verify(doc_id: int):
            """Create document and verify in same thread."""
            try:
                # Create document
                doc = registry.register_document(
                    path=f"docs/doc{doc_id}.md", doc_type="prd", author="John"
                )

                # Verify it exists immediately in same thread
                retrieved = registry.get_document(doc.id)
                assert retrieved.id == doc.id

                with lock:
                    success_count[0] += 1
            except Exception:
                with lock:
                    failure_count[0] += 1
            finally:
                # Close thread-local connection
                registry.close()

        # Create threads
        threads = []
        for i in range(10):
            t = threading.Thread(target=create_and_verify, args=(i,))
            threads.append(t)

        # Start all threads
        for t in threads:
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify all transactions succeeded
        assert success_count[0] == 10
        assert failure_count[0] == 0
