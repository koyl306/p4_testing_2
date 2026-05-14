import pytest
from httpx import AsyncClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app import models
from datetime import datetime, timedelta


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.mark.asyncio
async def test_create_book():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/books", json={
            "title": "Book1",
            "author": "Author1",
            "isbn": "123",
            "genre": "Fiction",
            "copies": 2
        })
        assert r.status_code == 200


@pytest.mark.asyncio
async def test_search_book_by_title():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        await ac.post("/books", json={"title": "ABC", "author": "A", "isbn": "1", "genre": "F", "copies": 1})
        r = await ac.get("/books?title=ABC")
        assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_borrow_book():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        b = await ac.post("/books", json={"title": "X", "author": "Y", "isbn": "2", "genre": "F", "copies": 1})
        book_id = b.json()["id"]

        r = await ac.post(f"/books/{book_id}/borrow", json={"user_id": 1})
        assert r.status_code == 200


@pytest.mark.asyncio
async def test_no_copies_available():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        b = await ac.post("/books", json={"title": "X", "author": "Y", "isbn": "2", "genre": "F", "copies": 1})
        book_id = b.json()["id"]

        await ac.post(f"/books/{book_id}/borrow", json={"user_id": 1})
        r = await ac.post(f"/books/{book_id}/borrow", json={"user_id": 2})

        assert r.status_code == 400


@pytest.mark.asyncio
async def test_return_book():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        b = await ac.post("/books", json={"title": "X", "author": "Y", "isbn": "2", "genre": "F", "copies": 1})
        book_id = b.json()["id"]

        await ac.post(f"/books/{book_id}/borrow", json={"user_id": 1})
        r = await ac.post(f"/books/{book_id}/return", json={"user_id": 1})

        assert r.status_code == 200


@pytest.mark.asyncio
async def test_availability():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        b = await ac.post("/books", json={"title": "X", "author": "Y", "isbn": "2", "genre": "F", "copies": 2})
        book_id = b.json()["id"]

        r = await ac.get(f"/books/{book_id}/availability")
        assert r.json()["available"] == 2


@pytest.mark.asyncio
async def test_borrowed_books():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        b = await ac.post("/books", json={"title": "X", "author": "Y", "isbn": "2", "genre": "F", "copies": 1})
        book_id = b.json()["id"]

        await ac.post(f"/books/{book_id}/borrow", json={"user_id": 1})
        r = await ac.get("/users/1/borrowed")

        assert len(r.json()) == 1

@pytest.mark.asyncio
async def test_filter_by_author():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        await ac.post("/books", json={"title": "A", "author": "Bob", "isbn": "1", "genre": "F", "copies": 1})
        r = await ac.get("/books?author=Bob")
        assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_filter_by_genre():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        await ac.post("/books", json={"title": "A", "author": "B", "isbn": "1", "genre": "SciFi", "copies": 1})
        r = await ac.get("/books?genre=SciFi")
        assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_borrow_and_availability_decrease():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        b = await ac.post("/books", json={"title": "A", "author": "B", "isbn": "1", "genre": "F", "copies": 2})
        book_id = b.json()["id"]

        await ac.post(f"/books/{book_id}/borrow", json={"user_id": 1})
        r = await ac.get(f"/books/{book_id}/availability")

        assert r.json()["available"] == 1


@pytest.mark.asyncio
async def test_return_restores_availability():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        b = await ac.post("/books", json={"title": "A", "author": "B", "isbn": "1", "genre": "F", "copies": 1})
        book_id = b.json()["id"]

        await ac.post(f"/books/{book_id}/borrow", json={"user_id": 1})
        await ac.post(f"/books/{book_id}/return", json={"user_id": 1})

        r = await ac.get(f"/books/{book_id}/availability")
        assert r.json()["available"] == 1

def test_get_overdue_books(db):
    result = getOverdueBooks(7, db)
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_book_not_found():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/books/999/availability")
        assert r.status_code == 404


@pytest.mark.asyncio
async def test_return_nonexistent_borrow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/books/1/return", json={"user_id": 1})
        assert r.status_code == 404


@pytest.mark.asyncio
async def test_multiple_users_borrow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        b = await ac.post("/books", json={
            "title": "Multi",
            "author": "A",
            "isbn": "55",
            "genre": "F",
            "copies": 2
        })

        book_id = b.json()["id"]

        r1 = await ac.post(f"/books/{book_id}/borrow", json={"user_id": 1})
        r2 = await ac.post(f"/books/{book_id}/borrow", json={"user_id": 2})

        assert r1.status_code == 200
        assert r2.status_code == 200


@pytest.mark.asyncio
async def test_empty_search_result():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/books?title=NOTFOUND")
        assert r.json() == []


@pytest.mark.asyncio
async def test_availability_after_two_borrows():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        b = await ac.post("/books", json={
            "title": "Copies",
            "author": "A",
            "isbn": "99",
            "genre": "F",
            "copies": 3
        })

        book_id = b.json()["id"]

        await ac.post(f"/books/{book_id}/borrow", json={"user_id": 1})
        await ac.post(f"/books/{book_id}/borrow", json={"user_id": 2})

        r = await ac.get(f"/books/{book_id}/availability")

        assert r.json()["available"] == 1