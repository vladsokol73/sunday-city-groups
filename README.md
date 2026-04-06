# Sunday City Groups

`Sunday City Groups` is a desktop application for Windows that helps clan leaders manage participants and generate balanced Sunday City group rosters.

The app is built with `Python`, `PySide6`, and `SQLite`, ships as an `exe` installer, and is tailored for real-world manual operations: clan member management, subgroup handling, party balancing, admin participation, and ready-to-paste exports for `VK` and `Telegram`.

## Highlights

- Dark desktop UI with a modern card-based layout
- Local SQLite storage, no server required
- Participant table with `nickname`, `Telegram`, `VK`, `name`, `birth date`, `role`, `party count`, and `preferred group`
- Named subgroups with editable titles
- One-click subgroup creation from selected participants
- Flexible grouping logic with support for:
  - admins participating in all groups
  - ordinary members staying in only one group
  - a maximum of `25` people per group
  - subgroup preservation unless group preferences explicitly conflict
  - maximizing total distributed parties while keeping groups as balanced as possible
- Copy-ready publication text for both `VK` and `Telegram`
- Seed script for generating `60` test participants

## Business Rules

- `party_count = null` means the participant does not attend
- `party_count = 0` means the participant attends but does not host parties
- admins with non-null party count are included in all groups
- ordinary participants belong to only one final group
- subgroup membership is respected by default
- preferred group is a strong preference, not an absolute lock
- if preferences inside a subgroup conflict, the subgroup can be split
- if total parties cannot be divided evenly, the app keeps as many balanced parties as possible and leaves only the unavoidable remainder outside the final plan

## Export Formats

After generation, the app produces:

- an internal detailed result view for manual review
- a ready-to-copy `VK` text block
- a ready-to-copy `Telegram` text block

Each export supports custom intro text and automatically adds party summary before the lists.

## Tech Stack

- `Python 3`
- `PySide6`
- `SQLite`
- `PyInstaller`
- `Inno Setup`

## Run Locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Or simply run:

```bash
run.bat
```

## Test Data

To fill the local database with `60` demo participants and prepared subgroups:

```bash
python seed_test_data.py
```

This overwrites current local test data in the app database.

## Build

### Build exe

```bash
pip install -r requirements.txt
build_exe.bat
```

### Build installer

```bash
build_installer.bat
```

The final installer is generated at:

```text
installer-output\SundayCityGroups-Setup.exe
```

## Data Storage

The application stores its database in:

```text
%LOCALAPPDATA%\SundayCityGroups\data\clan_manager.db
```

This keeps installed builds writable without requiring admin rights.

## Repository and Release Layout

Recommended publishing structure:

- source code in the GitHub repository
- `installer-output\SundayCityGroups-Setup.exe` attached to the GitHub Release

Temporary build artifacts are excluded from version control:

- `build/`
- `dist/`
- `*.spec`

## Status

The app is production-oriented for the described workflow and already includes:

- automated tests for grouping logic
- Windows installer packaging
- release-ready project cleanup

Future upgrades can still improve the optimization engine further, but the current version is already suitable for practical use and portfolio presentation.
