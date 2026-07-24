# Contributing

1. Create a focused branch.
2. Keep fixtures synthetic and small.
3. Add a unit test for behavior changes.
4. Run `python -m ruff check src tests`.
5. Run `python -m ruff format --check src tests`.
6. Run `python -m unittest discover -s tests -v`.
7. Run `pnpm run check`.
8. Confirm that no browser state, user files, or internal URLs are staged.

Changes to issue wording should preserve stable issue codes so exported data
remains comparable across versions.
