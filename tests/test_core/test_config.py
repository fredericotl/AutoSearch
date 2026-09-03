from app.core.config import Settings

def test_anchor_sqlite():
    result = Settings._anchor_sqlite("sqlite:///test.db")
    assert "test.db" in result
    assert "./" not in result

