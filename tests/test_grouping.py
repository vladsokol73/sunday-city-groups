import unittest

from app.grouping import generate_groups
from app.models import Participant, Subgroup


def make_participant(
    participant_id: int,
    nickname: str,
    party_count: int | None,
    role: str = "participant",
    preferred_group: int | None = None,
    secondary_preferred_group: int | None = None,
) -> Participant:
    return Participant(
        id=participant_id,
        nickname=nickname,
        telegram_nick="",
        vk_nick="",
        full_name="",
        birth_date=None,
        role=role,
        party_count=party_count,
        preferred_group=preferred_group,
        secondary_preferred_group=secondary_preferred_group,
    )


class GroupingTests(unittest.TestCase):
    def test_subgroup_members_stay_together(self) -> None:
        participants = [
            make_participant(1, "Alpha", 2),
            make_participant(2, "Beta", 1),
            make_participant(3, "Gamma", 3),
            make_participant(4, "Delta", 0),
        ]
        subgroups = [Subgroup(id=1, name="Основа", members=[participants[0], participants[1]])]

        result = generate_groups(participants, subgroups, group_count=2)

        groups_by_member = {}
        for group in result.groups:
            for member in group.members:
                groups_by_member[member.participant.id] = group.group_number

        self.assertEqual(groups_by_member[1], groups_by_member[2])

    def test_admin_parties_are_distributed_to_fill_targets(self) -> None:
        participants = [
            make_participant(1, "Alpha", 4),
            make_participant(2, "Beta", 2),
            make_participant(3, "Admin", 3, role="admin"),
        ]

        result = generate_groups(participants, [], group_count=3)

        self.assertEqual(result.target_parties_per_group, 3)
        totals = [group.total_parties for group in result.groups]
        self.assertEqual(sum(group.admin_parties for group in result.groups), 3)
        self.assertEqual(max(totals), 3)
        self.assertEqual(min(totals), 2)
        self.assertEqual(sum(group.member_parties for group in result.groups), 5)

    def test_member_group_parties_are_exposed(self) -> None:
        participants = [
            make_participant(1, "Alpha", 2),
            make_participant(2, "Beta", 1),
        ]

        result = generate_groups(participants, [], group_count=1)

        member_parties = {member.participant.nickname: member.parties_in_group for member in result.groups[0].members}
        self.assertEqual(member_parties["Alpha"], 2)
        self.assertEqual(member_parties["Beta"], 1)

    def test_56_parties_on_3_groups_becomes_18_each(self) -> None:
        participants = []
        participant_id = 1
        for _ in range(8):
            participants.append(make_participant(participant_id, f"Four{participant_id}", 4))
            participant_id += 1
        for _ in range(12):
            participants.append(make_participant(participant_id, f"Two{participant_id}", 2))
            participant_id += 1

        result = generate_groups(participants, [], group_count=3)

        self.assertEqual(result.target_parties_per_group, 18)
        self.assertEqual(result.dropped_parties, 2)
        self.assertEqual([group.total_parties for group in result.groups], [18, 18, 18])

    def test_regular_member_is_only_in_one_group(self) -> None:
        participants = [
            make_participant(1, "Alpha", 3),
            make_participant(2, "Beta", 3),
            make_participant(3, "Gamma", 3),
            make_participant(4, "Admin", 3, role="admin"),
        ]

        result = generate_groups(participants, [], group_count=3)

        seen = {}
        for group in result.groups:
            for member in group.members:
                nickname = member.participant.nickname
                seen[nickname] = seen.get(nickname, 0) + 1

        self.assertEqual(seen["Alpha"], 1)
        self.assertEqual(seen["Beta"], 1)
        self.assertEqual(seen["Gamma"], 1)

    def test_conflicting_group_preferences_can_split_subgroup(self) -> None:
        participants = [
            make_participant(1, "Alpha", 3, preferred_group=1),
            make_participant(2, "Beta", 3, preferred_group=2),
            make_participant(3, "Gamma", 3),
        ]
        subgroups = [Subgroup(id=1, name="Связка", members=participants)]

        result = generate_groups(participants, subgroups, group_count=2)

        placement = {}
        for group in result.groups:
            for member in group.members:
                placement[member.participant.nickname] = group.group_number

        self.assertEqual(placement["Alpha"], 1)
        self.assertEqual(placement["Beta"], 2)

    def test_primary_preference_wins_over_load_balancing_when_feasible(self) -> None:
        """Regression: preferences must not be sacrificed just to spread member parties."""
        participants = [
            make_participant(1, "Want1", 5, preferred_group=1),
            make_participant(2, "X_n", 5),
            make_participant(3, "Y_n", 5),
            make_participant(4, "Z_n", 5),
        ]

        result = generate_groups(participants, [], group_count=4)

        placement: dict[int, int] = {}
        for group in result.groups:
            for member in group.members:
                pid = member.participant.id
                if pid is not None:
                    placement[pid] = group.group_number

        self.assertEqual(placement[1], 1)

    def test_admin_parties_are_spread_when_possible(self) -> None:
        participants = [
            make_participant(1, "A1", 10),
            make_participant(2, "A2", 10),
            make_participant(3, "A3", 10),
            make_participant(4, "A4", 10),
            make_participant(5, "A5", 10),
            make_participant(6, "A6", 10),
            make_participant(7, "A7", 10),
            make_participant(8, "A8", 10),
            make_participant(9, "A9", 10),
            make_participant(10, "Admin", 9, role="admin"),
        ]

        result = generate_groups(participants, [], group_count=3)

        admin_totals = [group.admin_parties for group in result.groups]
        self.assertEqual(result.target_parties_per_group, 33)
        self.assertEqual(admin_totals, [3, 3, 3])


if __name__ == "__main__":
    unittest.main()
