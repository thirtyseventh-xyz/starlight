from sqlalchemy import DateTime, func, false
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    oidc_ident: Mapped[str]
    hca_token: Mapped[str]
    eligible: Mapped[bool]
    slack_id: Mapped[str]
    join_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    username: Mapped[str]
    associated_project: Mapped[int|None]
    admin: Mapped[bool] = mapped_column(default=False, server_default=false())