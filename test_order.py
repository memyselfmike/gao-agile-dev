from pathlib import Path
import tempfile
import time
from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.state_machine import DocumentStateMachine
from gao_dev.lifecycle.models import DocumentState

f = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
db_path = Path(f.name)
f.close()

registry = DocumentRegistry(db_path)
machine = DocumentStateMachine(registry)

doc = registry.register_document(path='test.md', doc_type='prd', author='test', state=DocumentState.DRAFT)

# DRAFT -> ACTIVE
machine.transition(doc, DocumentState.ACTIVE)
time.sleep(0.01)

# ACTIVE -> OBSOLETE
doc = registry.get_document(doc.id)
machine.transition(doc, DocumentState.OBSOLETE, reason='test')
time.sleep(0.01)

# OBSOLETE -> ARCHIVED
doc = registry.get_document(doc.id)
machine.transition(doc, DocumentState.ARCHIVED, reason='test')

history = machine.get_transition_history(doc.id)
print(f'History length: {len(history)}')
for i, h in enumerate(history):
    print(f'{i}: {h.from_state.value} -> {h.to_state.value} at {h.changed_at}')

db_path.unlink()
