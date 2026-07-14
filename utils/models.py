from sqlalchemy import DateTime, func, false, ARRAY, String, Table, Column, ForeignKey, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import datetime


class Base(DeclarativeBase):
    pass

user_project_association = Table(
    "user_project_association",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("project_id", ForeignKey("projects.id"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"

    id:                         Mapped[int] = mapped_column(primary_key=True)
    username:                   Mapped[str]
    slack_id:                   Mapped[str]

    oidc_ident:                 Mapped[str]
    hca_token:                  Mapped[str]
    hackatime_token:            Mapped[str|None]
    eligible:                   Mapped[bool]
    admin:                      Mapped[bool] = mapped_column(default=False, server_default=false())

    join_date:                  Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    associated_project:         Mapped[list["Project"]] = relationship(secondary=user_project_association, back_populates="users")

    last_session_clear_date:    Mapped[datetime.datetime|None] = mapped_column(DateTime(timezone=True))

class Project(Base):
    __tablename__ = "projects"

    id:                 Mapped[int] = mapped_column(primary_key=True)
    users:              Mapped[list["User"]] = relationship(secondary=user_project_association, back_populates="associated_project")

    category:           Mapped[str]
    slack_thread:       Mapped[str]

    hackatime_projects: Mapped[list[str]] = mapped_column(ARRAY(String))
    total_hours:        Mapped[int] = mapped_column(default=0,server_default="0")

    review_status:      Mapped[int] = mapped_column(default=0,server_default="0") #0 is not submitted, 1 is submitted but unreviewed, 2 is passed review
    # TODO:this ^^^ should probably be a dict with values at some point but i cba to right now


class ShopItem(Base):
    __tablename__ = "shop_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str]
    description: Mapped[str]

    orders: Mapped[list["ShopItem"]] = relationship(back_populates="item")

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)

    item: Mapped["ShopItem"] = relationship(back_populates="orders")
    item_id: Mapped[int] = mapped_column(ForeignKey("shop_items.id"))

