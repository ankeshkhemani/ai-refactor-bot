"""Database models for the AI Refactor Bot."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class Installation(Base):
    """GitHub App installation record."""

    __tablename__ = "installations"

    id = Column(Integer, primary_key=True)
    installation_id = Column(Integer, unique=True, nullable=False)
    account_id = Column(Integer, nullable=False)
    account_type = Column(String, nullable=False)  # 'User' or 'Organization'
    account_login = Column(String, nullable=False)
    target_type = Column(String, nullable=False)  # 'User' or 'Organization'
    target_id = Column(Integer, nullable=False)
    target_login = Column(String, nullable=False)
    repository_selection = Column(String, nullable=False)  # 'selected' or 'all'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    suspended_at = Column(DateTime, nullable=True)
    suspended_by = Column(Integer, nullable=True)
    repositories = relationship("Repository", back_populates="installation")


class Repository(Base):
    """GitHub repository record."""

    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, unique=True, nullable=False)
    name = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    private = Column(Boolean, nullable=False)
    owner_id = Column(Integer, nullable=False)
    owner_login = Column(String, nullable=False)
    installation_id = Column(Integer, ForeignKey("installations.installation_id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_analyzed_at = Column(DateTime, nullable=True)
    installation = relationship("Installation", back_populates="repositories")


# Database setup
def init_db(database_url: str):
    """Initialize the database."""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
