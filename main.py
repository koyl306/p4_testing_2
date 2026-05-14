from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from .database import Base, engine, get_db
from . import models

Base.metadata.create_all(bind=engine)

app = FastAPI()


# ---------- BOOKS ----------

@app.post("/books")
def create_book(book: dict, db: Session = Depends(get_db)):
    b = models.Book(**book)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


@app.get("/books")
def get_books(title: str = None, author: str = None, genre: str = None,
              db: Session = Depends(get_db)):
    q = db.query(models.Book)

    if title:
        q = q.filter(models.Book.title.contains(title))
    if author:
        q = q.filter(models.Book.author.contains(author))
    if genre:
        q = q.filter(models.Book.genre == genre)

    return q.all()


@app.get("/books/{book_id}/availability")
def availability(book_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).get(book_id)
    if not book:
        raise HTTPException(404)

    active_borrows = db.query(models.Borrow).filter(
        models.Borrow.book_id == book_id,
        models.Borrow.returned_at.is_(None)
    ).count()

    return {"available": book.copies - active_borrows}


@app.post("/books/{book_id}/borrow")
def borrow(book_id: int, payload: dict, db: Session = Depends(get_db)):
    user_id = payload["user_id"]
    book = db.query(models.Book).get(book_id)

    if not book:
        raise HTTPException(404)

    active = db.query(models.Borrow).filter(
        models.Borrow.book_id == book_id,
        models.Borrow.returned_at.is_(None)
    ).count()

    if active >= book.copies:
        raise HTTPException(400, "No copies available")

    borrow = models.Borrow(
        user_id=user_id,
        book_id=book_id,
        due_date=datetime.utcnow() + timedelta(days=14)
    )

    db.add(borrow)
    db.commit()
    return {"status": "borrowed"}


@app.post("/books/{book_id}/return")
def return_book(book_id: int, payload: dict, db: Session = Depends(get_db)):
    user_id = payload["user_id"]

    borrow = db.query(models.Borrow).filter_by(
        book_id=book_id,
        user_id=user_id,
        returned_at=None
    ).first()

    if not borrow:
        raise HTTPException(404)

    borrow.returned_at = datetime.utcnow()
    db.commit()

    return {"status": "returned"}


# ---------- USERS ----------

@app.get("/users/{user_id}/borrowed")
def borrowed(user_id: int, db: Session = Depends(get_db)):
    borrows = db.query(models.Borrow).filter_by(
        user_id=user_id,
        returned_at=None
    ).all()

    return borrows

def getOverdueBooks(days: int, db: Session):
    threshold = datetime.utcnow() - timedelta(days=days)

    return db.query(models.Borrow).filter(
        models.Borrow.returned_at.is_(None),
        models.Borrow.due_date < threshold
    ).all()