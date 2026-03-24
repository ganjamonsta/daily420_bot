"""Модели базы данных — SQLAlchemy (async, SQLite)."""
from __future__ import annotations

import datetime as _dt
from typing import Optional, List

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.core.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    """Telegram‑пользователь."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # tg user id
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    coins: Mapped[int] = mapped_column(Integer, default=0)
    total_harvests: Mapped[int] = mapped_column(Integer, default=0)
    total_buds: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[_dt.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    plants: Mapped[List["Plant"]] = relationship(back_populates="owner", lazy="selectin")
    inventory: Mapped[List["Inventory"]] = relationship(back_populates="owner", lazy="selectin")


class Plant(Base):
    """Растение пользователя (текущий гров)."""

    __tablename__ = "plants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    strain_key: Mapped[str] = mapped_column(String(64))
    custom_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    growth_points: Mapped[float] = mapped_column(Float, default=0.0)
    stage: Mapped[str] = mapped_column(String(32), default="seed")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_sick: Mapped[bool] = mapped_column(Boolean, default=False)
    sickness: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    mutated: Mapped[bool] = mapped_column(Boolean, default=False)
    mutation_strain: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    pot_color: Mapped[str] = mapped_column(String(32), default="🟤")
    energy: Mapped[int] = mapped_column(Integer, default=4)
    last_action_at: Mapped[Optional[_dt.datetime]] = mapped_column(DateTime, nullable=True)
    last_energy_reset: Mapped[_dt.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    started_at: Mapped[_dt.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    harvested_at: Mapped[Optional[_dt.datetime]] = mapped_column(DateTime, nullable=True)
    buds_yield: Mapped[int] = mapped_column(Integer, default=0)

    owner: Mapped["User"] = relationship(back_populates="plants")


class Inventory(Base):
    """Предметы пользователя (апгрейды из магазина)."""

    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    item_key: Mapped[str] = mapped_column(String(64))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    equipped: Mapped[bool] = mapped_column(Boolean, default=False)

    owner: Mapped["User"] = relationship(back_populates="inventory")


class HarvestLog(Base):
    """Лог харвестов для лидерборда."""

    __tablename__ = "harvest_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    strain_key: Mapped[str] = mapped_column(String(64))
    buds: Mapped[int] = mapped_column(Integer)
    harvested_at: Mapped[_dt.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


async def init_db() -> None:
    """Создаёт все таблицы."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
