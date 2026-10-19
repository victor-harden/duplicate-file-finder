# duplicate-file-finder

Find duplicate files under one or more directories. Files are grouped by size
first, then hashed with SHA-256, so large trees are handled without reading every
byte twice.

## Features

- Two-stage matching: size, then content hash.
- Groups sorted by wasted space.
- Read-only by default; `--delete` removes duplicates but keeps the first file of
  each group and requires confirmation unless `--yes` is passed.
- JSON output for reporting.
- Tests with temporary trees.

## Installation

```bash
git clone https://github.com/victor-harden/duplicate-file-finder.git
cd duplicate-file-finder
```

## Usage

```bash
python3 find_duplicates.py ~/Pictures
python3 find_duplicates.py ~/Pictures ~/Downloads --json
python3 find_duplicates.py ~/Pictures --delete --yes
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT — see [LICENSE](LICENSE).
