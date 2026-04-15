from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, QTimer, Qt
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.database import Database
from app.grouping import generate_groups
from app.models import GenerationResult, Participant, Subgroup


def _format_birth_date(value: str | None) -> str:
    if not value:
        return ""
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return value
    return parsed.strftime("%d.%m.%Y")


def _create_button(text: str, role: str | None = None) -> QPushButton:
    button = QPushButton(text)
    if role == "primary":
        button.setObjectName("primaryButton")
    elif role == "danger":
        button.setObjectName("dangerButton")
    return button


def _create_card(title: str, description: str) -> tuple[QFrame, QVBoxLayout]:
    card = QFrame()
    card.setObjectName("card")

    layout = QVBoxLayout(card)
    layout.setContentsMargins(20, 18, 20, 20)
    layout.setSpacing(14)

    title_label = QLabel(title)
    title_label.setObjectName("sectionTitle")
    description_label = QLabel(description)
    description_label.setObjectName("sectionDescription")
    description_label.setWordWrap(True)

    layout.addWidget(title_label)
    layout.addWidget(description_label)
    return card, layout


def _configure_table(table: QTableWidget) -> None:
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSelectionMode(QAbstractItemView.SingleSelection)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.verticalHeader().setVisible(False)
    table.setAlternatingRowColors(True)
    table.setShowGrid(False)
    table.setWordWrap(False)
    table.setFocusPolicy(Qt.StrongFocus)
    table.horizontalHeader().setHighlightSections(False)
    table.horizontalHeader().setStretchLastSection(False)
    table.verticalHeader().setDefaultSectionSize(34)


def _center_item(item: QTableWidgetItem) -> QTableWidgetItem:
    item.setTextAlignment(Qt.AlignCenter)
    return item


class StatCard(QFrame):
    def __init__(self, caption: str) -> None:
        super().__init__()
        self.setObjectName("statCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(2)

        self.value_label = QLabel("0")
        self.value_label.setObjectName("statValue")
        self.caption_label = QLabel(caption)
        self.caption_label.setObjectName("statCaption")

        layout.addWidget(self.value_label)
        layout.addWidget(self.caption_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class ParticipantDialog(QDialog):
    def __init__(self, participant: Participant | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Карточка участника")
        self.resize(520, 520)
        self.participant = participant

        self.nickname_edit = QLineEdit()
        self.nickname_edit.setPlaceholderText("Например: ShadowFox")
        self.telegram_edit = QLineEdit()
        self.telegram_edit.setPlaceholderText("@telegram_nick")
        self.vk_edit = QLineEdit()
        self.vk_edit.setPlaceholderText("vk_nick")
        self.full_name_edit = QLineEdit()
        self.full_name_edit.setPlaceholderText("Имя или заметка")

        self.birth_date_edit = QDateEdit()
        self.birth_date_edit.setCalendarPopup(True)
        self.birth_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.birth_date_edit.setDate(QDate.currentDate())

        self.birth_date_empty = QCheckBox("Дата рождения не указана")
        self.birth_date_empty.setChecked(True)
        self.birth_date_empty.toggled.connect(self.birth_date_edit.setDisabled)
        self.birth_date_edit.setDisabled(True)

        self.role_box = QComboBox()
        self.role_box.addItem("Участник", userData="participant")
        self.role_box.addItem("Админ", userData="admin")

        self.party_count_edit = QSpinBox()
        self.party_count_edit.setMinimum(0)
        self.party_count_edit.setMaximum(9999)
        self.party_count_null = QCheckBox("Не идет на пати (null)")
        self.party_count_null.setChecked(True)
        self.party_count_null.toggled.connect(self.party_count_edit.setDisabled)
        self.party_count_edit.setDisabled(True)

        self.preferred_group_edit = QSpinBox()
        self.preferred_group_edit.setMinimum(1)
        self.preferred_group_edit.setMaximum(999)
        self.preferred_group_null = QCheckBox("Предпочтение не указано")
        self.preferred_group_null.setChecked(True)
        self.preferred_group_null.toggled.connect(self.preferred_group_edit.setDisabled)
        self.preferred_group_edit.setDisabled(True)

        form_box = QGroupBox("Основные данные")
        form_layout = QFormLayout(form_box)
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignTop)
        form_layout.setContentsMargins(18, 22, 18, 18)
        form_layout.setSpacing(12)
        form_layout.addRow("Игровой ник", self.nickname_edit)
        form_layout.addRow("Ник в Telegram", self.telegram_edit)
        form_layout.addRow("Ник в VK", self.vk_edit)
        form_layout.addRow("Имя", self.full_name_edit)
        form_layout.addRow("Дата рождения", self.birth_date_edit)
        form_layout.addRow("", self.birth_date_empty)

        party_box = QGroupBox("Участие в группах")
        party_layout = QFormLayout(party_box)
        party_layout.setContentsMargins(18, 22, 18, 18)
        party_layout.setSpacing(12)
        party_layout.addRow("Роль", self.role_box)
        party_layout.addRow("Количество пати", self.party_count_edit)
        party_layout.addRow("", self.party_count_null)
        party_layout.addRow("Удобная группа", self.preferred_group_edit)
        party_layout.addRow("", self.preferred_group_null)

        helper_label = QLabel(
            "Обязательное поле только одно: игровой ник. Если пати = null, участник не идет в распределение."
        )
        helper_label.setObjectName("sectionDescription")
        helper_label.setWordWrap(True)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        ok_button = buttons.button(QDialogButtonBox.Ok)
        cancel_button = buttons.button(QDialogButtonBox.Cancel)
        if ok_button is not None:
            ok_button.setText("Сохранить")
            ok_button.setObjectName("primaryButton")
        if cancel_button is not None:
            cancel_button.setText("Отмена")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)
        layout.addWidget(form_box)
        layout.addWidget(party_box)
        layout.addWidget(helper_label)
        layout.addWidget(buttons)

        if participant is not None:
            self._fill_from_participant(participant)

    def _fill_from_participant(self, participant: Participant) -> None:
        self.nickname_edit.setText(participant.nickname)
        self.telegram_edit.setText(participant.telegram_nick)
        self.vk_edit.setText(participant.vk_nick)
        self.full_name_edit.setText(participant.full_name)
        self.role_box.setCurrentIndex(0 if participant.role == "participant" else 1)

        has_birth_date = participant.birth_date is not None
        self.birth_date_empty.setChecked(not has_birth_date)
        if has_birth_date:
            parsed = date.fromisoformat(participant.birth_date)
            self.birth_date_edit.setDate(QDate(parsed.year, parsed.month, parsed.day))

        has_party_count = participant.party_count is not None
        self.party_count_null.setChecked(not has_party_count)
        if has_party_count:
            self.party_count_edit.setValue(participant.party_count or 0)

        has_preferred_group = participant.preferred_group is not None
        self.preferred_group_null.setChecked(not has_preferred_group)
        if has_preferred_group:
            self.preferred_group_edit.setValue(participant.preferred_group or 1)

    def get_participant(self) -> Participant:
        nickname = self.nickname_edit.text().strip()
        if not nickname:
            raise ValueError("Игровой ник обязателен.")

        birth_date = None
        if not self.birth_date_empty.isChecked():
            birth_date = self.birth_date_edit.date().toPython().isoformat()

        party_count = None if self.party_count_null.isChecked() else self.party_count_edit.value()
        preferred_group = (
            None if self.preferred_group_null.isChecked() else self.preferred_group_edit.value()
        )

        if preferred_group is not None and party_count is None:
            raise ValueError("Нельзя указать удобную группу, если человек не идет на пати.")

        return Participant(
            id=self.participant.id if self.participant else None,
            nickname=nickname,
            telegram_nick=self.telegram_edit.text().strip(),
            vk_nick=self.vk_edit.text().strip(),
            full_name=self.full_name_edit.text().strip(),
            birth_date=birth_date,
            role=self.role_box.currentData(),
            party_count=party_count,
            preferred_group=preferred_group,
        )


class SubgroupDialog(QDialog):
    def __init__(
        self,
        participants: list[Participant],
        subgroup: Subgroup | None = None,
        preselected_ids: list[int] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Подгруппа")
        self.resize(760, 560)
        self.participants = participants
        self.subgroup = subgroup
        self.preselected_ids = set(preselected_ids or [])
        self.selected_ids: set[int] = set(self.preselected_ids)
        self.all_participants = list(participants)
        self.filtered_participants = list(participants)
        self._restoring_selection = False

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск участников (ник, Telegram, VK, имя)")
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(180)
        self.search_timer.timeout.connect(self._apply_filter)
        self.search_edit.textChanged.connect(lambda: self.search_timer.start())

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Например: Основа 1, Вечерняя пачка, Друзья")

        self.info_label = QLabel(
            "Выберите участников кликом по строкам. Один участник может состоять только в одной подгруппе."
        )
        self.info_label.setObjectName("sectionDescription")
        self.info_label.setWordWrap(True)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Ник", "Telegram", "VK", "Имя", "Текущая подгруппа"]
        )
        _configure_table(self.table)
        self.table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.table.setColumnHidden(0, True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        ok_button = buttons.button(QDialogButtonBox.Ok)
        cancel_button = buttons.button(QDialogButtonBox.Cancel)
        if ok_button is not None:
            ok_button.setText("Сохранить подгруппу")
            ok_button.setObjectName("primaryButton")
        if cancel_button is not None:
            cancel_button.setText("Отмена")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        card, card_layout = _create_card(
            "Настройка подгруппы",
            "Подгруппа будет учитываться при формировании игровых групп как единый связанный блок.",
        )
        form_layout = QFormLayout()
        form_layout.addRow("Название", self.name_edit)
        card_layout.addLayout(form_layout)
        card_layout.addWidget(self.info_label)
        card_layout.addWidget(self.search_edit)
        card_layout.addWidget(self.table)
        layout.addWidget(card)
        layout.addWidget(buttons)

        self._fill_data()

        self.table.itemSelectionChanged.connect(self._sync_persistent_selection_from_visible)

    def _fill_data(self) -> None:
        if self.subgroup is not None:
            self.name_edit.setText(self.subgroup.name)
            self.preselected_ids.update(member.id for member in self.subgroup.members if member.id is not None)
            self.selected_ids.update(self.preselected_ids)

        self._apply_filter()

    def _apply_filter(self) -> None:
        search_value = self.search_edit.text().strip().lower()
        if not search_value:
            self.filtered_participants = list(self.all_participants)
        else:
            self.filtered_participants = [
                participant
                for participant in self.all_participants
                if search_value
                in " ".join(
                    [
                        participant.nickname,
                        participant.telegram_nick,
                        participant.vk_nick,
                        participant.full_name,
                    ]
                ).lower()
            ]

        self._restoring_selection = True
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.filtered_participants))
        editable_subgroup_id = self.subgroup.id if self.subgroup else None

        for row, participant in enumerate(self.filtered_participants):
            values = [
                str(participant.id),
                participant.nickname,
                participant.telegram_nick,
                participant.vk_nick,
                participant.full_name,
                participant.subgroup_name or "",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                _center_item(item)
                if column == 5 and participant.subgroup_name:
                    item.setToolTip(f"Участник уже состоит в подгруппе «{participant.subgroup_name}».")
                self.table.setItem(row, column, item)

            participant_id = participant.id or -1
            in_other_subgroup = participant.subgroup_id is not None and participant.subgroup_id != editable_subgroup_id
            if in_other_subgroup:
                for column in range(self.table.columnCount()):
                    cell = self.table.item(row, column)
                    if cell is not None:
                        cell.setFlags(cell.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEnabled)
            elif participant_id in self.selected_ids:
                self.table.selectRow(row)

        self.table.resizeRowsToContents()
        self.table.blockSignals(False)
        self._restoring_selection = False
        self._sync_persistent_selection_from_visible()

    def _sync_persistent_selection_from_visible(self) -> None:
        if self._restoring_selection:
            return

        visible_ids: set[int] = set()
        visible_selected_ids: set[int] = set()

        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is None:
                continue
            participant_id = int(item.text())
            visible_ids.add(participant_id)
            if self.table.selectionModel().isRowSelected(row, self.table.rootIndex()):
                visible_selected_ids.add(participant_id)

        # Remove items that are visible but not selected anymore.
        self.selected_ids.difference_update(visible_ids - visible_selected_ids)
        # Add currently selected visible items.
        self.selected_ids.update(visible_selected_ids)

    def selected_participant_ids(self) -> list[int]:
        self._sync_persistent_selection_from_visible()
        return sorted(self.selected_ids)

    def get_payload(self) -> tuple[str, list[int]]:
        name = self.name_edit.text().strip()
        if not name:
            raise ValueError("Укажите название подгруппы.")
        participant_ids = self.selected_participant_ids()
        if len(participant_ids) < 2:
            raise ValueError("Для подгруппы нужно выбрать минимум двух участников.")
        return name, participant_ids


class ParticipantsTab(QWidget):
    HEADERS = [
        "ID",
        "Ник",
        "Telegram",
        "VK",
        "Имя",
        "Дата рождения",
        "Роль",
        "Пати",
        "Удобная группа",
        "Подгруппа",
    ]

    def __init__(self, database: Database, main_window: "MainWindow") -> None:
        super().__init__()
        self.database = database
        self.main_window = main_window
        self.all_participants: list[Participant] = []
        self.selected_ids: set[int] = set()
        self._filtered_ids: set[int] = set()
        self._restoring_selection = False

        self.total_label = QLabel("0 записей")
        self.total_label.setObjectName("sectionDescription")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по нику, Telegram, VK, имени или подгруппе")
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(180)
        self.search_timer.timeout.connect(self._apply_filter)
        self.search_edit.textChanged.connect(lambda: self.search_timer.start())

        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        _configure_table(self.table)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setColumnHidden(0, True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)
        for column in (2, 3, 5, 6, 7, 8):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
        self.table.itemSelectionChanged.connect(self._sync_persistent_selection_from_visible)

        self.add_button = _create_button("Добавить", "primary")
        self.edit_button = _create_button("Изменить")
        self.delete_button = _create_button("Удалить", "danger")
        self.create_subgroup_button = _create_button("Создать подгруппу из выбранных")
        self.reset_parties_button = _create_button("Сбросить всем пати в 0")
        self.refresh_button = _create_button("Обновить")

        self.add_button.clicked.connect(self.add_participant)
        self.edit_button.clicked.connect(self.edit_selected_participant)
        self.delete_button.clicked.connect(self.delete_selected_participant)
        self.create_subgroup_button.clicked.connect(self.create_subgroup_from_selection)
        self.reset_parties_button.clicked.connect(self.reset_all_parties_to_zero)
        self.refresh_button.clicked.connect(self.main_window.refresh_all)

        toolbar_card, toolbar_layout = _create_card(
            "Список участников",
            "Ведите основную таблицу клана. Поле с ником обязательно, остальные данные можно заполнять по мере надобности.",
        )
        toolbar_row = QHBoxLayout()
        toolbar_row.setSpacing(10)
        toolbar_row.addWidget(self.total_label)
        toolbar_row.addWidget(self.search_edit, stretch=1)
        toolbar_row.addWidget(self.add_button)
        toolbar_row.addWidget(self.edit_button)
        toolbar_row.addWidget(self.delete_button)
        toolbar_row.addWidget(self.create_subgroup_button)
        toolbar_row.addWidget(self.reset_parties_button)
        toolbar_row.addWidget(self.refresh_button)
        toolbar_layout.addLayout(toolbar_row)

        table_card, table_layout = _create_card(
            "Таблица",
            "Роли, пати и предпочтительная группа используются при генерации итоговых игровых групп.",
        )
        table_layout.addWidget(self.table)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(toolbar_card)
        layout.addWidget(table_card)

    def refresh(self) -> None:
        self.all_participants = self.database.list_participants()
        self._apply_filter()

    def _apply_filter(self) -> None:
        # persist selection before rebuilding
        self._sync_persistent_selection_from_visible()

        search_value = self.search_edit.text().strip().lower()
        filtered_participants = [
            participant
            for participant in self.all_participants
            if not search_value
            or search_value in " ".join(
                [
                    participant.nickname,
                    participant.telegram_nick,
                    participant.vk_nick,
                    participant.full_name,
                    participant.subgroup_name or "",
                ]
            ).lower()
        ]

        self.total_label.setText(f"{len(filtered_participants)} из {len(self.all_participants)} записей")
        self._filtered_ids = {p.id for p in filtered_participants if p.id is not None}
        self._restoring_selection = True
        self.table.blockSignals(True)
        self.table.setRowCount(len(filtered_participants))

        for row, participant in enumerate(filtered_participants):
            values = [
                str(participant.id),
                participant.nickname,
                participant.telegram_nick,
                participant.vk_nick,
                participant.full_name,
                _format_birth_date(participant.birth_date),
                "Админ" if participant.role == "admin" else "Участник",
                "null" if participant.party_count is None else str(participant.party_count),
                "" if participant.preferred_group is None else str(participant.preferred_group),
                participant.subgroup_name or "",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                self.table.setItem(row, column, item)
                _center_item(item)

            if participant.id is not None and participant.id in self.selected_ids:
                self.table.selectRow(row)

        self.table.blockSignals(False)
        self._restoring_selection = False
        self._sync_persistent_selection_from_visible()

    def _sync_persistent_selection_from_visible(self) -> None:
        if self._restoring_selection:
            return
        model = self.table.selectionModel()
        if model is None:
            return

        visible_selected_ids = {
            int(self.table.item(index.row(), 0).text())
            for index in model.selectedRows()
            if self.table.item(index.row(), 0) is not None
        }

        # Remove items that are currently visible but no longer selected.
        self.selected_ids.difference_update(self._filtered_ids - visible_selected_ids)
        # Add selected visible items.
        self.selected_ids.update(visible_selected_ids)

    def _selected_participant_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def _selected_participant_ids(self) -> list[int]:
        # persistent selection across searches
        self._sync_persistent_selection_from_visible()
        return sorted(self.selected_ids)

    def add_participant(self) -> None:
        dialog = ParticipantDialog(parent=self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            participant = dialog.get_participant()
            self.database.save_participant(participant)
        except ValueError as error:
            QMessageBox.warning(self, "Ошибка", str(error))
            return
        self.main_window.refresh_all()

    def edit_selected_participant(self) -> None:
        participant_id = self._selected_participant_id()
        if participant_id is None:
            QMessageBox.information(self, "Подсказка", "Сначала выберите строку с участником.")
            return

        participant = self.database.get_participant(participant_id)
        if participant is None:
            QMessageBox.warning(self, "Ошибка", "Участник не найден.")
            return

        dialog = ParticipantDialog(participant=participant, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            updated_participant = dialog.get_participant()
            self.database.save_participant(updated_participant)
        except ValueError as error:
            QMessageBox.warning(self, "Ошибка", str(error))
            return
        self.main_window.refresh_all()

    def delete_selected_participant(self) -> None:
        participant_id = self._selected_participant_id()
        if participant_id is None:
            QMessageBox.information(self, "Подсказка", "Сначала выберите строку с участником.")
            return

        answer = QMessageBox.question(
            self,
            "Удалить участника",
            "Удалить выбранного участника и все его связи?",
        )
        if answer != QMessageBox.Yes:
            return

        self.database.delete_participant(participant_id)
        self.main_window.refresh_all()

    def create_subgroup_from_selection(self) -> None:
        selected_ids = self._selected_participant_ids()
        if len(selected_ids) < 2:
            QMessageBox.information(
                self,
                "Подсказка",
                "Выделите минимум двух участников в таблице и затем создайте подгруппу.",
            )
            return

        dialog = SubgroupDialog(
            participants=self.database.list_participants(),
            preselected_ids=selected_ids,
            parent=self,
        )
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            name, participant_ids = dialog.get_payload()
            self.database.create_subgroup(name, participant_ids)
        except ValueError as error:
            QMessageBox.warning(self, "Ошибка", str(error))
            return
        self.main_window.refresh_all()

    def reset_all_parties_to_zero(self) -> None:
        answer = QMessageBox.question(
            self,
            "Сбросить пати",
            "Сбросить всем участникам значение пати до 0?\n\nЭто изменит и тех, у кого сейчас стоит null.",
        )
        if answer != QMessageBox.Yes:
            return
        self.database.reset_all_party_counts_to_zero()
        self.main_window.refresh_all()


class SubgroupsTab(QWidget):
    def __init__(self, database: Database, main_window: "MainWindow") -> None:
        super().__init__()
        self.database = database
        self.main_window = main_window

        self.all_subgroups: list[Subgroup] = []
        self.subgroup_rows: list[Subgroup] = []
        self.subgroups_count_label = QLabel("0 подгрупп")
        self.subgroups_count_label.setObjectName("sectionDescription")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск подгруппы по названию")
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(180)
        self.search_timer.timeout.connect(self._apply_filter)
        self.search_edit.textChanged.connect(lambda: self.search_timer.start())

        self.subgroups_table = QTableWidget(0, 4)
        self.subgroups_table.setHorizontalHeaderLabels(["ID", "Подгруппа", "Состав", "Участников"])
        _configure_table(self.subgroups_table)
        self.subgroups_table.setColumnHidden(0, True)
        header = self.subgroups_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        add_button = _create_button("Создать вручную", "primary")
        edit_button = _create_button("Изменить")
        remove_button = _create_button("Удалить", "danger")
        add_button.clicked.connect(self.add_subgroup)
        edit_button.clicked.connect(self.edit_selected_subgroup)
        remove_button.clicked.connect(self.remove_selected_subgroup)

        table_card, table_layout = _create_card(
            "Подгруппы и связи",
            "Здесь видно, какие участники уже объединены вместе. Название подгруппы можно менять в любой момент.",
        )
        actions = QHBoxLayout()
        actions.addWidget(self.subgroups_count_label)
        actions.addWidget(self.search_edit, stretch=1)
        actions.addWidget(add_button)
        actions.addWidget(edit_button)
        actions.addWidget(remove_button)
        table_layout.addLayout(actions)
        table_layout.addWidget(self.subgroups_table)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(table_card)

    def refresh(self) -> None:
        self.all_subgroups = self.database.list_subgroups()
        self._apply_filter()

    def _apply_filter(self) -> None:
        search_value = self.search_edit.text().strip().lower()
        self.subgroup_rows = [
            subgroup
            for subgroup in self.all_subgroups
            if not search_value or search_value in subgroup.name.lower()
        ]
        self.subgroups_count_label.setText(f"{len(self.subgroup_rows)} из {len(self.all_subgroups)} подгрупп")
        self.subgroups_table.setRowCount(len(self.subgroup_rows))
        for row, subgroup in enumerate(self.subgroup_rows):
            member_names = ", ".join(member.nickname for member in subgroup.members)
            values = [str(subgroup.id), subgroup.name, member_names, str(len(subgroup.members))]
            for column, value in enumerate(values):
                self.subgroups_table.setItem(row, column, _center_item(QTableWidgetItem(value)))

    def _selected_subgroup(self) -> Subgroup | None:
        row = self.subgroups_table.currentRow()
        if row < 0:
            return None
        subgroup_id = int(self.subgroups_table.item(row, 0).text())
        for subgroup in self.subgroup_rows:
            if subgroup.id == subgroup_id:
                return subgroup
        return None

    def add_subgroup(self) -> None:
        dialog = SubgroupDialog(participants=self.database.list_participants(), parent=self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            name, participant_ids = dialog.get_payload()
            self.database.create_subgroup(name, participant_ids)
        except ValueError as error:
            QMessageBox.warning(self, "Ошибка", str(error))
            return
        self.main_window.refresh_all()

    def edit_selected_subgroup(self) -> None:
        subgroup = self._selected_subgroup()
        if subgroup is None:
            QMessageBox.information(self, "Подсказка", "Сначала выберите подгруппу в таблице.")
            return

        dialog = SubgroupDialog(
            participants=self.database.list_participants(),
            subgroup=subgroup,
            parent=self,
        )
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            name, participant_ids = dialog.get_payload()
            self.database.update_subgroup(subgroup.id or 0, name, participant_ids)
        except ValueError as error:
            QMessageBox.warning(self, "Ошибка", str(error))
            return
        self.main_window.refresh_all()

    def remove_selected_subgroup(self) -> None:
        subgroup = self._selected_subgroup()
        if subgroup is None:
            QMessageBox.information(self, "Подсказка", "Сначала выберите подгруппу в таблице.")
            return
        answer = QMessageBox.question(
            self,
            "Удалить подгруппу",
            f"Удалить подгруппу «{subgroup.name}»?",
        )
        if answer != QMessageBox.Yes:
            return
        self.database.delete_subgroup(subgroup.id or 0)
        self.main_window.refresh_all()


class GeneratorTab(QWidget):
    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self.last_result: GenerationResult | None = None

        self.group_count_edit = QSpinBox()
        self.group_count_edit.setMinimum(1)
        self.group_count_edit.setMaximum(50)
        self.group_count_edit.setValue(3)

        self.generate_button = _create_button("Сформировать группы", "primary")
        self.generate_button.clicked.connect(self.generate)

        self.result_view = QTextEdit()
        self.result_view.setReadOnly(True)
        self.result_view.setPlaceholderText("Здесь появится итог распределения по группам.")

        self.vk_intro_edit = QTextEdit()
        self.vk_intro_edit.setPlaceholderText("Введите текст, который будет стоять перед списками для VK.")
        self.vk_intro_edit.setFixedHeight(86)
        self.vk_intro_edit.textChanged.connect(self.refresh_exports)

        self.telegram_intro_edit = QTextEdit()
        self.telegram_intro_edit.setPlaceholderText("Введите текст, который будет стоять перед списками для Telegram.")
        self.telegram_intro_edit.setFixedHeight(86)
        self.telegram_intro_edit.textChanged.connect(self.refresh_exports)

        self.vk_output = QTextEdit()
        self.vk_output.setReadOnly(True)
        self.telegram_output = QTextEdit()
        self.telegram_output.setReadOnly(True)

        self.copy_vk_button = _create_button("Скопировать текст для VK")
        self.copy_tg_button = _create_button("Скопировать текст для Telegram")
        self.copy_vk_button.clicked.connect(lambda: self._copy_text(self.vk_output))
        self.copy_tg_button.clicked.connect(lambda: self._copy_text(self.telegram_output))

        controls_card, controls_layout = _create_card(
            "Параметры генерации",
            "Укажите количество групп и запустите генерацию. Главный приоритет алгоритма — как можно ровнее распределить пати между группами.",
        )
        controls_row = QHBoxLayout()
        controls_row.setSpacing(12)
        controls_row.addWidget(QLabel("Количество групп"))
        controls_row.addWidget(self.group_count_edit)
        controls_row.addWidget(self.generate_button)
        controls_row.addStretch()
        controls_layout.addLayout(controls_row)

        export_card, export_layout = _create_card(
            "Тексты для публикации",
            "Подготовьте отдельные вступления для VK и Telegram. После генерации можно сразу скопировать готовый список.",
        )
        export_grid = QGridLayout()
        export_grid.setHorizontalSpacing(16)
        export_grid.setVerticalSpacing(12)
        export_grid.addWidget(QLabel("Вступление для VK"), 0, 0)
        export_grid.addWidget(QLabel("Вступление для Telegram"), 0, 1)
        export_grid.addWidget(self.vk_intro_edit, 1, 0)
        export_grid.addWidget(self.telegram_intro_edit, 1, 1)
        export_layout.addLayout(export_grid)

        result_card, result_layout = _create_card(
            "Результат",
            "Внутренний результат остается в полном виде, а рядом доступны два готовых текста для публикации в VK и Telegram.",
        )
        self.output_tabs = QTabWidget()
        self.output_tabs.addTab(self.result_view, "Результат")

        vk_tab = QWidget()
        vk_layout = QVBoxLayout(vk_tab)
        vk_layout.setContentsMargins(0, 0, 0, 0)
        vk_layout.setSpacing(12)
        vk_layout.addWidget(self.copy_vk_button, alignment=Qt.AlignLeft)
        vk_layout.addWidget(self.vk_output)

        tg_tab = QWidget()
        tg_layout = QVBoxLayout(tg_tab)
        tg_layout.setContentsMargins(0, 0, 0, 0)
        tg_layout.setSpacing(12)
        tg_layout.addWidget(self.copy_tg_button, alignment=Qt.AlignLeft)
        tg_layout.addWidget(self.telegram_output)

        self.output_tabs.addTab(vk_tab, "Текст для VK")
        self.output_tabs.addTab(tg_tab, "Текст для Telegram")
        result_layout.addWidget(self.output_tabs)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(controls_card)
        layout.addWidget(export_card)
        layout.addWidget(result_card)

    def refresh(self) -> None:
        if not self.result_view.toPlainText():
            self.result_view.setPlainText(
                "Добавьте участников, настройте связи и затем нажмите «Сформировать группы»."
            )
        if not self.vk_output.toPlainText():
            self.vk_output.setPlainText("После генерации здесь появится текст для VK.")
        if not self.telegram_output.toPlainText():
            self.telegram_output.setPlainText("После генерации здесь появится текст для Telegram.")

    def generate(self) -> None:
        participants = self.database.list_participants()
        subgroups = self.database.list_subgroups()
        try:
            result = generate_groups(participants, subgroups, self.group_count_edit.value())
        except ValueError as error:
            QMessageBox.warning(self, "Ошибка", str(error))
            return

        self.last_result = result
        self.result_view.setPlainText(self._format_result(result))
        self.refresh_exports()

    def refresh_exports(self) -> None:
        if self.last_result is None:
            return
        self.vk_output.setPlainText(
            self._format_platform_text(self.last_result, "vk", self.vk_intro_edit.toPlainText())
        )
        self.telegram_output.setPlainText(
            self._format_platform_text(
                self.last_result, "telegram", self.telegram_intro_edit.toPlainText()
            )
        )

    def _copy_text(self, text_edit: QTextEdit) -> None:
        text = text_edit.toPlainText().strip()
        if not text:
            return
        QApplication.clipboard().setText(text)

    def _format_result(self, result: GenerationResult) -> str:
        lines = [
            f"Всего пати в расчете: {result.total_parties}",
            f"Целевое количество пати на группу: {result.target_parties_per_group}",
            f"Оставлено вне распределения: {result.dropped_parties}",
            "",
        ]

        if result.warnings:
            lines.append("Предупреждения:")
            for warning in result.warnings:
                lines.append(f"- {warning}")
            lines.append("")

        for group in result.groups:
            lines.append(
                f"Группа {group.group_number}: всего пати {group.total_parties} "
                f"(участники {group.member_parties}, админы {group.admin_parties})"
            )
            if group.members:
                lines.append("Участники:")
                for member in group.members:
                    participant = member.participant
                    preferred_group = (
                        f", удобна группа {participant.preferred_group}"
                        if participant.preferred_group is not None
                        else ""
                    )
                    lines.append(
                        f"  - {participant.nickname} [{member.subgroup_label}]"
                        f" | пати в этой группе: {member.parties_in_group}{preferred_group}"
                    )
            else:
                lines.append("Участники: нет")

            if group.admins:
                lines.append("Админы:")
                for admin in group.admins:
                    participant = admin.participant
                    party_count = "null" if participant.party_count is None else str(participant.party_count)
                    lines.append(
                        f"  - {participant.nickname} | всего пати: {party_count}, "
                        f"в этой группе: {admin.parties_in_group}, неиспользовано: {admin.unused_parties}"
                    )
            else:
                lines.append("Админы: нет")
            lines.append("")

        return "\n".join(lines).strip()

    def _format_platform_text(
        self,
        result: GenerationResult,
        platform: str,
        intro_text: str,
    ) -> str:
        lines: list[str] = []
        if intro_text.strip():
            lines.append(intro_text.strip())
            lines.append("")

        lines.append(f"Всего {result.total_parties} пати, в каждой группе: {result.target_parties_per_group} пати.")

        for group in result.groups:
            lines.extend(["", f"{group.group_number} группа"])
            index = 1
            for member in group.members:
                participant = member.participant
                contact = self._contact_for_platform(participant, platform)
                lines.append(
                    f"{index}. {participant.nickname}, {contact}, {member.parties_in_group} пати"
                )
                index += 1

            for admin in group.admins:
                participant = admin.participant
                contact = self._contact_for_platform(participant, platform)
                lines.append(
                    f"{index}. {participant.nickname} (админ), {contact}, {admin.parties_in_group} пати"
                )
                index += 1

        return "\n".join(lines).strip()

    @staticmethod
    def _contact_for_platform(participant: Participant, platform: str) -> str:
        if platform == "vk":
            return participant.vk_nick or participant.full_name or participant.nickname
        return participant.telegram_nick or participant.full_name or participant.nickname


class MainWindow(QMainWindow):
    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self.setWindowTitle("Sunday City Groups")
        self.resize(1280, 820)

        self.tabs = QTabWidget()
        self.participants_tab = ParticipantsTab(database, self)
        self.links_tab = SubgroupsTab(database, self)
        self.generator_tab = GeneratorTab(database)

        self.tabs.addTab(self.participants_tab, "Участники")
        self.tabs.addTab(self.links_tab, "Подгруппы")
        self.tabs.addTab(self.generator_tab, "Генерация групп")

        self.total_participants_card = StatCard("Всего участников")
        self.active_parties_card = StatCard("Идут на пати")
        self.admins_card = StatCard("Администраторы")
        self.links_card = StatCard("Подгруппы")

        hero_card = QFrame()
        hero_card.setObjectName("heroCard")
        hero_layout = QVBoxLayout(hero_card)
        hero_layout.setContentsMargins(24, 22, 24, 22)
        hero_layout.setSpacing(10)

        title_label = QLabel("Sunday City Groups")
        title_label.setObjectName("pageTitle")
        subtitle_label = QLabel(
            "Тёмная рабочая панель для учёта состава клана, связей между участниками и генерации игровых групп."
        )
        subtitle_label.setObjectName("pageSubtitle")
        subtitle_label.setWordWrap(True)

        hero_layout.addWidget(title_label)
        hero_layout.addWidget(subtitle_label)

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(14)
        stats_layout.addWidget(self.total_participants_card)
        stats_layout.addWidget(self.active_parties_card)
        stats_layout.addWidget(self.admins_card)
        stats_layout.addWidget(self.links_card)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)
        layout.addWidget(hero_card)
        layout.addLayout(stats_layout)
        layout.addWidget(self.tabs)
        self.setCentralWidget(container)

        self.refresh_all()

    def refresh_all(self) -> None:
        self.participants_tab.refresh()
        self.links_tab.refresh()
        self.generator_tab.refresh()
        self._refresh_dashboard()

    def _refresh_dashboard(self) -> None:
        participants = self.database.list_participants()
        subgroups = self.database.list_subgroups()
        active_participants = [participant for participant in participants if participant.party_count is not None]
        admins = [participant for participant in participants if participant.role == "admin"]

        self.total_participants_card.set_value(str(len(participants)))
        self.active_parties_card.set_value(str(len(active_participants)))
        self.admins_card.set_value(str(len(admins)))
        self.links_card.set_value(str(len(subgroups)))
