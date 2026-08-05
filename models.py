from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
    UUID(as_uuid=True),
    nullable=False,
    index=True,
)
    title = Column(String, nullable=False, default="New Conversation")
    language = Column(String, nullable=False, default="German")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
    UUID(as_uuid=True),
    nullable=False,
    index=True,
)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    conversation = relationship(
        "Conversation",
        back_populates="messages",
    )


class FlashcardSet(Base):
    __tablename__ = "flashcard_sets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
    UUID(as_uuid=True),
    nullable=False,
    index=True,
)
    name = Column(String, nullable=False)
    language = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    journal_entry_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    flashcards = relationship(
        "Flashcard",
        back_populates="flashcard_set",
        cascade="all, delete-orphan",
    )


class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
    UUID(as_uuid=True),
    nullable=False,
    index=True,
)

    set_id = Column(
        Integer,
        ForeignKey("flashcard_sets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    front = Column(Text, nullable=False)
    back = Column(Text, nullable=False)
    language = Column(String, nullable=False, default="German")
    mastered = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    flashcard_set = relationship(
        "FlashcardSet",
        back_populates="flashcards",
    )


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
    UUID(as_uuid=True),
    nullable=False,
    index=True,
)
    original_text = Column(Text, nullable=False)
    corrected_text = Column(Text, nullable=False)
    mistakes = Column(JSON, nullable=False, default=list)
    target_language = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )


class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    icon = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    user_badges = relationship(
        "UserBadge",
        back_populates="badge",
        cascade="all, delete-orphan",
    )


class UserBadge(Base):
    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    badge_id = Column(
        Integer,
        ForeignKey("badges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    earned_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    badge = relationship(
        "Badge",
        back_populates="user_badges",
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "badge_id",
            name="uq_user_badge",
        ),
    )


class UserActivity(Base):
    __tablename__ = "user_activities"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    activity_type = Column(
        String,
        nullable=False,
        index=True,
    )

    activity_data = Column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True,
    )