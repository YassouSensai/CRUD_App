import uuid
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from flask_wtf import FlaskForm
from wtforms import StringField, DateField, BooleanField
from wtforms.validators import DataRequired, Optional, Length

# Connexion à la base de données
SQLALCHEMY_DATABASE_URL = "sqlite:///./todo.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()



class SearchForm(FlaskForm):
    """
    Classe SearchForm pour valider les données de recherche.

    Args:
        FlaskForm: Formulaire Flask
    """
    search = StringField('Search', validators=[DataRequired()])




class TodoForm(FlaskForm):
    """
    Classe TodoForm pour valider les données de création et de mise à jour des tâches.

    Args:
        FlaskForm: Formulaire Flask
    """
    task = StringField("Task", validators=[DataRequired(), Length(min=2, max=50)])
    due = DateField("Due Date", validators=[DataRequired()])
    complete = BooleanField("Complete")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'todo' not in kwargs:
            self.task.validators.append(DataRequired())



class Todo(Base):
    """
    class Todo

    Args:
        Base: Classe de base pour les classes de modèle SQLAlchemy
    """
    __tablename__ = 'todos'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task = Column(String)
    complete = Column(Boolean, default=False)
    due = Column(DateTime, default=datetime.utcnow)

# Initialisation de la base de données
def init_db():
    Base.metadata.create_all(bind=engine)

# Fonctions CRUD
def create_todo(task: str, complete: bool = False, due: datetime | None = None):
    db = SessionLocal()
    db_todo = Todo(task=task, complete=complete, due=due)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

def get_todo(todo_id: str):
    db = SessionLocal()
    return db.query(Todo).filter(Todo.id == todo_id).first()

def get_todo_by_name(name):
    db = SessionLocal()
    todos = db.query(Todo).filter(Todo.task.like(f"%{name}%")).all()
    return todos



def get_all_todos():
    db = SessionLocal()
    return db.query(Todo).all()

def update_todo(todo_id: str, task: str, complete: bool, due: datetime | None):
    db = SessionLocal()
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    db_todo.task = task
    db_todo.complete = complete
    db_todo.due = due
    db.commit()
    db.refresh(db_todo)
    return db_todo

def delete_todo(todo_id: str):
    db = SessionLocal()
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    db.delete(db_todo)
    db.commit()
    return db_todo
