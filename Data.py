from sqlalchemy import Column, Integer, String, LargeBinary,create_engine
from sqlalchemy.orm import declarative_base
Base=declarative_base()
class Document(Base):
    __tablename__= 'documents'
    id= Column(Integer, primary_key=True)
    text=Column(String)
    embedding= Column(LargeBinary)
Database_url = "postgresql://artisusxiren:Newpass@localhost/database_user"
engine=create_engine(Database_url)
Base.metadata.create_all(engine)
    