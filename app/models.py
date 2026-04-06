from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Participant:
    id: int | None
    nickname: str
    telegram_nick: str
    vk_nick: str
    full_name: str
    birth_date: str | None
    role: str
    party_count: int | None
    preferred_group: int | None
    subgroup_id: int | None = None
    subgroup_name: str | None = None


@dataclass(slots=True)
class Subgroup:
    id: int | None
    name: str
    members: list[Participant] = field(default_factory=list)


@dataclass(slots=True)
class GroupMember:
    participant: Participant
    subgroup_label: str
    parties_in_group: int


@dataclass(slots=True)
class AdminDistribution:
    participant: Participant
    parties_in_group: int
    unused_parties: int


@dataclass(slots=True)
class GroupPlan:
    group_number: int
    member_parties: int
    admin_parties: int
    members: list[GroupMember] = field(default_factory=list)
    admins: list[AdminDistribution] = field(default_factory=list)

    @property
    def total_parties(self) -> int:
        return self.member_parties + self.admin_parties


@dataclass(slots=True)
class GenerationResult:
    target_parties_per_group: int
    total_parties: int
    dropped_parties: int
    warnings: list[str]
    groups: list[GroupPlan]
