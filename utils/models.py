from sqlalchemy import DateTime, func, false, ARRAY, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id:                     Mapped[int] = mapped_column(primary_key=True)
    username:               Mapped[str]
    slack_id:               Mapped[str]

    oidc_ident:             Mapped[str]
    hca_token:              Mapped[str]
    eligible:               Mapped[bool]
    admin:                  Mapped[bool] = mapped_column(default=False, server_default=false())

    join_date:              Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    associated_project_id:  Mapped[int|None] = mapped_column(ForeignKey("projects.id"))
    associated_project:     Mapped["Project|None"] = relationship(back_populates="users")

class Project(Base):
    __tablename__ = "projects"

    id:                 Mapped[int] = mapped_column(primary_key=True)
    users:              Mapped[list["User"]] = relationship(back_populates="associated_project")

    category:           Mapped[str]
    slack_thread:       Mapped[str]
    hackatime_projects: Mapped[list[str]] = mapped_column(ARRAY(String))