from app.main import getOverdueBooks


def test_get_overdue_books(db):
    result = getOverdueBooks(7, db)
    assert isinstance(result, list)