from __future__ import annotations

import random
import sqlite3

from app.database import Database
from app.models import Participant
from app.paths import get_database_path


def reset_database() -> None:
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("DELETE FROM subgroup_members")
        connection.execute("DELETE FROM subgroups")
        connection.execute("DELETE FROM participant_links")
        connection.execute("DELETE FROM participants")
        connection.commit()
    finally:
        connection.close()


def build_participant(index: int, role: str, party_count: int | None, preferred_group: int | None) -> Participant:
    return Participant(
        id=None,
        nickname=f"Player{index:02d}",
        telegram_nick=f"@player{index:02d}" if index % 7 else "",
        vk_nick=f"idplayer{index:02d}" if index % 5 else "",
        full_name=f"Тестер {index:02d}",
        birth_date=None if index % 6 else f"199{index % 10}-0{(index % 9) + 1}-1{index % 9}",
        role=role,
        party_count=party_count,
        preferred_group=preferred_group,
    )


def main() -> None:
    random.seed(42)
    reset_database()
    database = Database()

    created_nicknames: list[str] = []
    for index in range(1, 61):
        role = "admin" if index in {3, 9, 18, 27, 36, 48} else "participant"

        if index in {5, 11, 19, 28, 41, 55}:
            party_count = None
        elif role == "admin":
            party_count = random.randint(3, 8)
        else:
            party_count = random.randint(0, 4)

        preferred_group = None if party_count is None else random.randint(1, 4)
        participant = build_participant(index, role, party_count, preferred_group)
        database.save_participant(participant)
        created_nicknames.append(participant.nickname)

    participants = {participant.nickname: participant for participant in database.list_participants()}

    subgroup_specs = [
        ("Основа 1", ["Player01", "Player02", "Player04"]),
        ("Основа 2", ["Player06", "Player07", "Player08"]),
        ("Друзья A", ["Player10", "Player12"]),
        ("Друзья B", ["Player13", "Player14", "Player15"]),
        ("Ночной слот", ["Player16", "Player17", "Player20", "Player21"]),
        ("VK Team", ["Player22", "Player23", "Player24"]),
        ("Telegram Team", ["Player25", "Player26"]),
        ("Старички", ["Player29", "Player30", "Player31"]),
        ("Утренние", ["Player32", "Player33", "Player34", "Player35"]),
        ("Вечерние", ["Player37", "Player38", "Player39"]),
        ("Костяк", ["Player42", "Player43", "Player44"]),
        ("Новички", ["Player45", "Player46", "Player47", "Player49"]),
    ]

    for name, nicknames in subgroup_specs:
        member_ids = [participants[nickname].id for nickname in nicknames if nickname in participants]
        database.create_subgroup(name, [member_id for member_id in member_ids if member_id is not None])

    print("Тестовые данные созданы.")
    print(f"База: {get_database_path()}")
    print("Участников: 60")
    print(f"Подгрупп: {len(subgroup_specs)}")


if __name__ == "__main__":
    main()
