import os
import tempfile
import pytest

# Every test session works on its own copy of the seed registry.
_TMP = tempfile.mkdtemp(prefix='skill-registry-')
os.environ['SKILL_REGISTRY'] = os.path.join(_TMP, 'registry')
os.environ.pop('ANTHROPIC_API_KEY', None)


@pytest.fixture
def reg():
    from app.main import REG
    REG.reset()
    REG.reload()
    return REG
