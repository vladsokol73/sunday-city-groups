from __future__ import annotations

import sqlite3
from collections import defaultdict
from pathlib import Path

from app.models import Participant, Subgroup
from app.paths import get_database_path


class Database:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or get_database_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS participants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nickname TEXT NOT NULL,
                    telegram_nick TEXT NOT NULL DEFAULT '',
                    vk_nick TEXT NOT NULL DEFAULT '',
                    full_name TEXT NOT NULL DEFAULT '',
                    birth_date TEXT,
                    role TEXT NOT NULL DEFAULT 'participant',
                    party_count INTEGER,
                    preferred_group INTEGER,
                    CHECK (role IN ('participant', 'admin')),
                    CHECK (party_count IS NULL OR party_count >= 0),
                    CHECK (preferred_group IS NULL OR preferred_group >= 1)
                );

                CREATE TABLE IF NOT EXISTS participant_links (
                    left_id INTEGER NOT NULL,
                    right_id INTEGER NOT NULL,
                    PRIMARY KEY (left_id, right_id),
                    FOREIGN KEY (left_id) REFERENCES participants(id) ON DELETE CASCADE,
                    FOREIGN KEY (right_id) REFERENCES participants(id) ON DELETE CASCADE,
                    CHECK (left_id < right_id)
                );

                CREATE TABLE IF NOT EXISTS subgroups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS subgroup_members (
                    subgroup_id INTEGER NOT NULL,
                    participant_id INTEGER NOT NULL UNIQUE,
                    PRIMARY KEY (subgroup_id, participant_id),
                    FOREIGN KEY (subgroup_id) REFERENCES subgroups(id) ON DELETE CASCADE,
                    FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE
                );
                """
            )
            self._migrate_legacy_links(connection)

    def list_participants(self) -> list[Participant]:
        with self._connect() as connection:
            rows = connection.execute(
                f"{self._participants_base_select_sql()} ORDER BY p.nickname COLLATE NOCASE, p.full_name COLLATE NOCASE"
            ).fetchall()
        return [self._participant_from_row(row) for row in rows]

    def get_participant(self, participant_id: int) -> Participant | None:
        with self._connect() as connection:
            row = connection.execute(
                f"{self._participants_base_select_sql()} WHERE p.id = ?",
                (participant_id,),
            ).fetchone()
        return self._participant_from_row(row) if row else None

    def save_participant(self, participant: Participant) -> None:
        values = (
            participant.nickname.strip(),
            participant.telegram_nick.strip(),
            participant.vk_nick.strip(),
            participant.full_name.strip(),
            participant.birth_date,
            participant.role,
            participant.party_count,
            participant.preferred_group,
        )
        with self._connect() as connection:
            if participant.id is None:
                connection.execute(
                    """
                    INSERT INTO participants (
                        nickname, telegram_nick, vk_nick, full_name,
                        birth_date, role, party_count, preferred_group
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    values,
                )
            else:
                connection.execute(
                    """
                    UPDATE participants
                    SET nickname = ?, telegram_nick = ?, vk_nick = ?, full_name = ?,
                        birth_date = ?, role = ?, party_count = ?, preferred_group = ?
                    WHERE id = ?
                    """,
                    (*values, participant.id),
                )

    def delete_participant(self, participant_id: int) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM participants WHERE id = ?", (participant_id,))
            self._delete_small_subgroups(connection)

    def reset_all_party_counts_to_zero(self) -> None:
        with self._connect() as connection:
            connection.execute("UPDATE participants SET party_count = NULL")

    def list_subgroups(self) -> list[Subgroup]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT s.id AS subgroup_id,
                       s.name AS subgroup_name,
                       p.id,
                       p.nickname,
                       p.telegram_nick,
                       p.vk_nick,
                       p.full_name,
                       p.birth_date,
                       p.role,
                       p.party_count,
                       p.preferred_group
                FROM subgroups AS s
                JOIN subgroup_members AS sm ON sm.subgroup_id = s.id
                JOIN participants AS p ON p.id = sm.participant_id
                ORDER BY s.name COLLATE NOCASE, p.nickname COLLATE NOCASE
                """
            ).fetchall()

        subgroup_map: dict[int, Subgroup] = {}
        for row in rows:
            subgroup_id = row["subgroup_id"]
            subgroup = subgroup_map.setdefault(
                subgroup_id,
                Subgroup(id=subgroup_id, name=row["subgroup_name"], members=[]),
            )
            subgroup.members.append(
                Participant(
                    id=row["id"],
                    nickname=row["nickname"],
                    telegram_nick=row["telegram_nick"],
                    vk_nick=row["vk_nick"],
                    full_name=row["full_name"],
                    birth_date=row["birth_date"],
                    role=row["role"],
                    party_count=row["party_count"],
                    preferred_group=row["preferred_group"],
                    subgroup_id=subgroup_id,
                    subgroup_name=row["subgroup_name"],
                )
            )
        return list(subgroup_map.values())

    def create_subgroup(self, name: str, participant_ids: list[int]) -> int:
        participant_ids = self._normalize_member_ids(participant_ids)
        with self._connect() as connection:
            self._validate_subgroup(connection, participant_ids, subgroup_id=None)
            cursor = connection.execute(
                "INSERT INTO subgroups (name) VALUES (?)",
                (name.strip() or "Новая подгруппа",),
            )
            subgroup_id = int(cursor.lastrowid)
            connection.executemany(
                "INSERT INTO subgroup_members (subgroup_id, participant_id) VALUES (?, ?)",
                [(subgroup_id, participant_id) for participant_id in participant_ids],
            )
        return subgroup_id

    def update_subgroup(self, subgroup_id: int, name: str, participant_ids: list[int]) -> None:
        participant_ids = self._normalize_member_ids(participant_ids)
        with self._connect() as connection:
            self._validate_subgroup(connection, participant_ids, subgroup_id=subgroup_id)
            connection.execute("UPDATE subgroups SET name = ? WHERE id = ?", (name.strip(), subgroup_id))
            connection.execute("DELETE FROM subgroup_members WHERE subgroup_id = ?", (subgroup_id,))
            connection.executemany(
                "INSERT INTO subgroup_members (subgroup_id, participant_id) VALUES (?, ?)",
                [(subgroup_id, participant_id) for participant_id in participant_ids],
            )

    def delete_subgroup(self, subgroup_id: int) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM subgroups WHERE id = ?", (subgroup_id,))

    @staticmethod
    def _normalize_member_ids(participant_ids: list[int]) -> list[int]:
        normalized = sorted(set(participant_ids))
        if len(normalized) < 2:
            raise ValueError("В подгруппе должно быть минимум 2 участника.")
        return normalized

    def _validate_subgroup(
        self,
        connection: sqlite3.Connection,
        participant_ids: list[int],
        subgroup_id: int | None,
    ) -> None:
        placeholders = ",".join("?" for _ in participant_ids)
        existing_rows = connection.execute(
            f"""
            SELECT participant_id, subgroup_id
            FROM subgroup_members
            WHERE participant_id IN ({placeholders})
            """,
            participant_ids,
        ).fetchall()
        for row in existing_rows:
            if subgroup_id is None or row["subgroup_id"] != subgroup_id:
                raise ValueError("Один из выбранных участников уже состоит в другой подгруппе.")

        participants_count = connection.execute(
            f"SELECT COUNT(*) FROM participants WHERE id IN ({placeholders})",
            participant_ids,
        ).fetchone()[0]
        if participants_count != len(participant_ids):
            raise ValueError("Не удалось найти всех выбранных участников.")

    def _migrate_legacy_links(self, connection: sqlite3.Connection) -> None:
        subgroup_count = connection.execute("SELECT COUNT(*) FROM subgroups").fetchone()[0]
        if subgroup_count:
            return

        link_rows = connection.execute(
            "SELECT left_id, right_id FROM participant_links ORDER BY left_id, right_id"
        ).fetchall()
        if not link_rows:
            return

        adjacency: dict[int, set[int]] = defaultdict(set)
        for row in link_rows:
            adjacency[row["left_id"]].add(row["right_id"])
            adjacency[row["right_id"]].add(row["left_id"])

        visited: set[int] = set()
        subgroup_index = 1
        for participant_id in sorted(adjacency):
            if participant_id in visited:
                continue
            stack = [participant_id]
            component: list[int] = []
            visited.add(participant_id)
            while stack:
                current_id = stack.pop()
                component.append(current_id)
                for neighbour_id in adjacency[current_id]:
                    if neighbour_id not in visited:
                        visited.add(neighbour_id)
                        stack.append(neighbour_id)
            if len(component) < 2:
                continue

            cursor = connection.execute(
                "INSERT INTO subgroups (name) VALUES (?)",
                (f"Подгруппа {subgroup_index}",),
            )
            subgroup_id = int(cursor.lastrowid)
            connection.executemany(
                "INSERT INTO subgroup_members (subgroup_id, participant_id) VALUES (?, ?)",
                [(subgroup_id, member_id) for member_id in sorted(component)],
            )
            subgroup_index += 1

    def _delete_small_subgroups(self, connection: sqlite3.Connection) -> None:
        subgroup_ids = connection.execute(
            """
            SELECT s.id
            FROM subgroups AS s
            LEFT JOIN subgroup_members AS sm ON sm.subgroup_id = s.id
            GROUP BY s.id
            HAVING COUNT(sm.participant_id) < 2
            """
        ).fetchall()
        for row in subgroup_ids:
            connection.execute("DELETE FROM subgroups WHERE id = ?", (row["id"],))

    @staticmethod
    def _participants_base_select_sql() -> str:
        return """
            SELECT p.id,
                   p.nickname,
                   p.telegram_nick,
                   p.vk_nick,
                   p.full_name,
                   p.birth_date,
                   p.role,
                   p.party_count,
                   p.preferred_group,
                   s.id AS subgroup_id,
                   s.name AS subgroup_name
            FROM participants AS p
            LEFT JOIN subgroup_members AS sm ON sm.participant_id = p.id
            LEFT JOIN subgroups AS s ON s.id = sm.subgroup_id
        """

    @staticmethod
    def _participant_from_row(row: sqlite3.Row) -> Participant:
        return Participant(
            id=row["id"],
            nickname=row["nickname"],
            telegram_nick=row["telegram_nick"],
            vk_nick=row["vk_nick"],
            full_name=row["full_name"],
            birth_date=row["birth_date"],
            role=row["role"],
            party_count=row["party_count"],
            preferred_group=row["preferred_group"],
            subgroup_id=row["subgroup_id"] if "subgroup_id" in row.keys() else None,
            subgroup_name=row["subgroup_name"] if "subgroup_name" in row.keys() else None,
        )
