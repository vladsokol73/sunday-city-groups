from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from app.models import (
    AdminDistribution,
    GenerationResult,
    GroupMember,
    GroupPlan,
    Participant,
    Subgroup,
)

MAX_GROUP_SIZE = 25

# Placement costs: strongly prefer satisfying primary, then secondary, then balance loads.
_PRIMARY_MATCH = 0
_SECONDARY_MATCH = 50
_NO_PREFERENCE = 0
_MISMATCH_PENALTY = 1_000_000


@dataclass(slots=True)
class _Component:
    label: str
    members: list[Participant]
    party_total: int
    preference_counts: dict[int, int] = field(default_factory=dict)

    @property
    def size(self) -> int:
        return len(self.members)


@dataclass(slots=True)
class _WorkingGroup:
    number: int
    members: list[GroupMember] = field(default_factory=list)
    member_parties: int = 0
    admin_parties: int = 0

    @property
    def member_count(self) -> int:
        return len(self.members)

    @property
    def total_parties(self) -> int:
        return self.member_parties + self.admin_parties


def generate_groups(
    participants: list[Participant],
    subgroups: list[Subgroup],
    group_count: int,
) -> GenerationResult:
    if group_count < 1:
        raise ValueError("Количество групп должно быть больше нуля.")

    active_participants = [participant for participant in participants if participant.party_count is not None]
    admins = [participant for participant in active_participants if participant.role == "admin"]
    regular_members = [
        participant for participant in active_participants if participant.role != "admin"
    ]

    total_parties = sum(participant.party_count or 0 for participant in active_participants)
    components = _build_components(regular_members, subgroups)
    warnings: list[str] = []
    admin_count = len(admins)
    admin_total_parties = sum(admin.party_count or 0 for admin in admins)
    regular_capacity = max(0, MAX_GROUP_SIZE - admin_count)
    target = total_parties // group_count if group_count else 0
    groups = [_WorkingGroup(number=index + 1) for index in range(group_count)]

    if admin_count > MAX_GROUP_SIZE:
        warnings.append(
            f"Админов, идущих на пати, больше лимита группы ({admin_count} > {MAX_GROUP_SIZE})."
        )

    skipped_components = _assign_all_components_to_groups(
        components=components,
        groups=groups,
        target=target,
        regular_capacity=regular_capacity,
    )
    _cap_member_parties_to_target(groups, target)

    admin_allocations = _distribute_admin_parties(admins, groups, target)
    used_parties = sum(group.total_parties for group in groups)
    dropped_parties = max(0, total_parties - used_parties)

    if skipped_components:
        skipped_people = sum(component.size for component in skipped_components)
        warnings.append(
            f"Часть обычных участников не попала в итоговые группы: {skipped_people} чел."
        )

    if dropped_parties:
        warnings.append(
            f"Не все пати можно распределить поровну: {dropped_parties} останутся вне итогового плана."
        )

    if any(group.total_parties != target for group in groups) and total_parties > 0:
        warnings.append(
            "Точное равенство по пати недостижимо с текущими связями и входными данными. Показан лучший найденный вариант."
        )

    if not active_participants:
        warnings.append("Сейчас нет участников с непустым значением пати, поэтому группы пустые.")

    result_groups: list[GroupPlan] = []
    for group in groups:
        admins_for_group: list[AdminDistribution] = []
        for admin in admins:
            allocations = admin_allocations.get(admin.id or -1, [0] * group_count)
            parties_in_group = allocations[group.number - 1]
            unused_parties = max(0, (admin.party_count or 0) - sum(allocations))
            admins_for_group.append(
                AdminDistribution(
                    participant=admin,
                    parties_in_group=parties_in_group,
                    unused_parties=unused_parties,
                )
            )

        result_groups.append(
            GroupPlan(
                group_number=group.number,
                member_parties=group.member_parties,
                admin_parties=group.admin_parties,
                members=group.members,
                admins=admins_for_group,
            )
        )

    return GenerationResult(
        target_parties_per_group=target,
        total_parties=total_parties,
        dropped_parties=dropped_parties,
        warnings=warnings,
        groups=result_groups,
    )


def _build_components(
    participants: list[Participant], subgroups: list[Subgroup]
) -> list[_Component]:
    participants_by_id = {participant.id: participant for participant in participants if participant.id is not None}
    components: list[_Component] = []
    assigned_ids: set[int] = set()

    for subgroup in sorted(subgroups, key=lambda item: (item.name.lower(), item.id or 0)):
        members = [
            participants_by_id[member.id]
            for member in subgroup.members
            if member.id in participants_by_id and member.id not in assigned_ids
        ]
        if not members:
            continue
        assigned_ids.update(member.id for member in members if member.id is not None)
        components.extend(_components_from_subgroup(members, subgroup.name))

    for participant in sorted(participants_by_id.values(), key=lambda item: item.nickname.lower()):
        if participant.id in assigned_ids:
            continue
        components.append(_component_from_members([participant], participant.subgroup_name or participant.nickname))

    components.sort(key=lambda component: (component.party_total, component.size), reverse=True)
    return components


def _component_from_members(members: list[Participant], label: str) -> _Component:
    preference_counts: dict[int, int] = defaultdict(int)
    for member in members:
        if member.preferred_group is not None:
            # Primary preference has higher weight than fallback.
            preference_counts[member.preferred_group] += 2
        if member.secondary_preferred_group is not None:
            preference_counts[member.secondary_preferred_group] += 1
    members = sorted(members, key=lambda item: item.nickname.lower())
    return _Component(
        label=label,
        members=members,
        party_total=sum(member.party_count or 0 for member in members),
        preference_counts=dict(preference_counts),
    )


def _components_from_subgroup(members: list[Participant], subgroup_name: str) -> list[_Component]:
    preferred_groups = {member.preferred_group for member in members if member.preferred_group is not None}
    if len(preferred_groups) <= 1:
        return [_component_from_members(members, subgroup_name)]

    components: list[_Component] = []
    for preferred_group in sorted(preferred_groups):
        preferred_members = [member for member in members if member.preferred_group == preferred_group]
        if preferred_members:
            components.append(
                _component_from_members(
                    preferred_members,
                    f"{subgroup_name} -> группа {preferred_group}",
                )
            )

    neutral_members = [member for member in members if member.preferred_group is None]
    if neutral_members:
        components.append(_component_from_members(neutral_members, f"{subgroup_name} (без предпочтения)"))

    return components


def _assign_components_to_groups(
    components: list[_Component],
    groups: list[_WorkingGroup],
    target: int,
) -> None:
    raise NotImplementedError("Используйте _build_best_distribution() вместо прямого назначения.")


def _assign_all_components_to_groups(
    components: list[_Component],
    groups: list[_WorkingGroup],
    target: int,
    regular_capacity: int,
    ) -> list[_Component]:
    if not groups:
        return list(components)

    total_members = sum(component.size for component in components)
    ideal_group_size = total_members / len(groups) if groups else 0
    skipped_components: list[_Component] = []

    for component in components:
        best_group: _WorkingGroup | None = None
        best_score: tuple[float, ...] | None = None

        for group in groups:
            future_member_count = group.member_count + component.size
            if future_member_count > regular_capacity:
                continue

            future_member_parties = group.member_parties + component.party_total
            future_loads = [
                future_member_parties if current_group.number == group.number else current_group.member_parties
                for current_group in groups
            ]
            max_load_after = max(future_loads)
            min_load_after = min(future_loads)
            load_spread_after = max_load_after - min_load_after
            over_target = max(0, future_member_parties - target)
            distance_to_target = abs(target - future_member_parties)
            size_distance = abs(ideal_group_size - future_member_count)
            preference_cost = _component_preference_cost(component, group.number)

            # preference_cost must dominate load-balancing so we only sacrifice preferences
            # when capacity forces it or when no preference was set.
            score = (
                preference_cost,
                max_load_after,
                load_spread_after,
                over_target,
                distance_to_target,
                size_distance,
                group.member_count,
                group.number,
            )

            if best_score is None or score < best_score:
                best_score = score
                best_group = group

        if best_group is None:
            skipped_components.append(component)
            continue

        _place_component_in_group(component, best_group)

    return skipped_components


def _member_preference_cost(member: Participant, group_number: int) -> int:
    primary = member.preferred_group
    secondary = member.secondary_preferred_group

    if primary is None and secondary is None:
        return _NO_PREFERENCE

    # Only fallback specified: treat it like the main wish.
    if primary is None and secondary is not None:
        return _PRIMARY_MATCH if group_number == secondary else _MISMATCH_PENALTY

    if group_number == primary:
        return _PRIMARY_MATCH

    if secondary is not None and group_number == secondary:
        return _SECONDARY_MATCH

    return _MISMATCH_PENALTY


def _component_preference_cost(component: _Component, group_number: int) -> int:
    return sum(_member_preference_cost(member, group_number) for member in component.members)


def _place_component_in_group(component: _Component, group: _WorkingGroup) -> None:
    group.member_parties += component.party_total
    for member in component.members:
        group.members.append(
            GroupMember(
                participant=member,
                subgroup_label=component.label,
                parties_in_group=member.party_count or 0,
            )
        )


def _cap_member_parties_to_target(groups: list[_WorkingGroup], target: int) -> None:
    for group in groups:
        overflow = max(0, group.member_parties - target)
        if overflow <= 0:
            continue

        adjustable_members = sorted(
            [member for member in group.members if member.parties_in_group > 0],
            key=lambda item: item.parties_in_group,
            reverse=True,
        )
        for member in adjustable_members:
            if overflow <= 0:
                break
            reduction = min(member.parties_in_group, overflow)
            member.parties_in_group -= reduction
            overflow -= reduction

        group.member_parties = sum(member.parties_in_group for member in group.members)


def _distribute_admin_parties(
    admins: list[Participant],
    groups: list[_WorkingGroup],
    target: int,
) -> dict[int, list[int]]:
    allocations: dict[int, list[int]] = {}

    for admin in admins:
        admin_id = admin.id
        if admin_id is None:
            continue

        remaining = admin.party_count or 0
        per_group = [0] * len(groups)

        while remaining > 0:
            candidate_groups = [group for group in groups if target - group.total_parties > 0]
            if not candidate_groups:
                break

            best_group = min(
                candidate_groups,
                key=lambda group: (
                    -(target - group.total_parties),
                    group.admin_parties,
                    group.total_parties,
                    group.member_count,
                    group.number,
                ),
            )
            deficit = target - best_group.total_parties
            if deficit <= 0:
                break

            best_group.admin_parties += 1
            per_group[best_group.number - 1] += 1
            remaining -= 1

        allocations[admin_id] = per_group

    return allocations
