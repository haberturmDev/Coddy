from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from domain.models.conversation import Conversation, Message, Role
from domain.ports.session_store import SessionStore
from infrastructure.sqlite.models import MessageRecord, SessionRecord


class SQLiteSessionStore(SessionStore):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_or_create(self, session_id: str) -> Conversation:
        with Session(self._engine) as sess:
            stmt = select(SessionRecord).where(SessionRecord.session_id == session_id)
            record = sess.scalar(stmt)
            if record is None:
                now = datetime.now(timezone.utc)
                record = SessionRecord(
                    session_id=session_id,
                    system_prompt="You are a helpful assistant.",
                    created_at=now,
                )
                sess.add(record)
                sess.commit()
                return Conversation(
                    messages=[],
                    system_prompt=record.system_prompt,
                )

            msg_stmt = (
                select(MessageRecord)
                .where(MessageRecord.session_id == session_id)
                .order_by(MessageRecord.created_at, MessageRecord.id)
            )
            rows = sess.scalars(msg_stmt).all()
            messages = [
                Message(
                    role=Role(row.role),
                    content=row.content,
                    created_at=row.created_at,
                )
                for row in rows
            ]
            return Conversation(
                messages=messages,
                system_prompt=record.system_prompt,
            )

    def save(self, session_id: str, conversation: Conversation) -> None:
        with Session(self._engine) as sess:
            record = sess.scalar(
                select(SessionRecord).where(SessionRecord.session_id == session_id)
            )
            if record is None:
                raise ValueError(
                    f"Session {session_id!r} not found; call get_or_create first."
                )
            record.system_prompt = conversation.system_prompt

            existing = sess.scalar(
                select(func.count())
                .select_from(MessageRecord)
                .where(MessageRecord.session_id == session_id)
            )
            existing = existing or 0
            for msg in conversation.messages[existing:]:
                sess.add(
                    MessageRecord(
                        session_id=session_id,
                        role=msg.role.value,
                        content=msg.content,
                        created_at=msg.created_at,
                    )
                )
            sess.commit()
