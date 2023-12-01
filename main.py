from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import databases
import sqlalchemy

DATABASE_URL = "postgresql://postgres:admin@localhost:5432/bookservices"

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

books = sqlalchemy.Table(
    "books",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, index=True),
    sqlalchemy.Column("title", sqlalchemy.String),
    # Add other columns as needed
)

authors = sqlalchemy.Table(
    "authors",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, index=True),
    sqlalchemy.Column("name", sqlalchemy.String),
    # Add other columns as needed
)

clients = sqlalchemy.Table(
    "clients",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, index=True),
    sqlalchemy.Column("name", sqlalchemy.String),
    # Add other columns as needed
)

books_authors = sqlalchemy.Table(
    "books_authors",
    metadata,
    sqlalchemy.Column("book_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("books.id")),
    sqlalchemy.Column("author_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("authors.id")),
)

books_clients = sqlalchemy.Table(
    "books_clients",
    metadata,
    sqlalchemy.Column("book_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("books.id")),
    sqlalchemy.Column("client_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("clients.id")),
)

engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(bind=engine)

class BookCreate(BaseModel):
    title: str
    author_ids: list[int]

class BookUpdate(BaseModel):
    title: str
    author_ids: list[int]

class AuthorCreate(BaseModel):
    name: str

class ClientCreate(BaseModel):
    name: str

app = FastAPI()

@app.post("/books/", response_model=dict)
async def create_book(book: BookCreate):
    query = books.insert().values(title=book.title)
    book_id = await database.execute(query)
    for author_id in book.author_ids:
        query = books_authors.insert().values(book_id=book_id, author_id=author_id)
        await database.execute(query)
    return {"id": book_id, **book.dict()}

@app.put("/books/{book_id}", response_model=dict)
async def update_book(book_id: int, book: BookUpdate):
    query = books.update().where(books.c.id == book_id).values(title=book.title)
    await database.execute(query)
    query = books_authors.delete().where(books_authors.c.book_id == book_id)
    await database.execute(query)
    for author_id in book.author_ids:
        query = books_authors.insert().values(book_id=book_id, author_id=author_id)
        await database.execute(query)
    return {"id": book_id, **book.dict()}

@app.get("/books/", response_model=list[dict])
async def get_books(title_startswith: str = None, author_id: int = None):
    query = books.select()
    if title_startswith:
        query = query.where(books.c.title.startswith(title_startswith))
    if author_id:
        query = query.where(books_authors.c.author_id == author_id)
    result = await database.fetch_all(query)
    return result

@app.post("/authors/", response_model=dict)
async def create_author(author: AuthorCreate):
    query = authors.insert().values(name=author.name)
    author_id = await database.execute(query)
    return {"id": author_id, **author.dict()}

@app.post("/clients/", response_model=dict)
async def create_client(client: ClientCreate):
    query = clients.insert().values(name=client.name)
    client_id = await database.execute(query)
    return {"id": client_id, **client.dict()}

@app.get("/clients/{client_id}/books/", response_model=list[dict])
async def get_client_books(client_id: int):
    query = books_clients.select().where(books_clients.c.client_id == client_id)
    result = await database.fetch_all(query)
    return result

@app.post("/clients/{client_id}/books/{book_id}/link/", response_model=dict)
async def link_client_book(client_id: int, book_id: int):
    query = books_clients.insert().values(client_id=client_id, book_id=book_id)
    await database.execute(query)
    return {"client_id": client_id, "book_id": book_id}

@app.post("/clients/{client_id}/books/{book_id}/unlink/", response_model=dict)
async def unlink_client_book(client_id: int, book_id: int):
    query = books_clients.delete().where(
        sqlalchemy.and_(books_clients.c.client_id == client_id, books_clients.c.book_id == book_id)
    )
    await database.execute(query)
    return {"client_id": client_id, "book_id": book_id}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

# ---------------------------------- Books route ----------------------------------



# ---------------------------------- Books route ----------------------------------