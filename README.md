# RPGE — reference implementation for Art01

Code snapshot that accompanies the paper *RPG-Based Behavioral Operators for Evolutionary Algorithms: A Formal Framework for Individualized Search Strategies* (RPGE): five-channel attribute sheet (STR, WIS, END, DEX, LCK),
behavioral modes dispatched by the dominant channel, XP-based progression and
the five-sector class scheme. The constants of the paper are the constants of
this snapshot.

This repository is a frozen snapshot of the paper's code, taken from the
authors' working repository. Variants and applications that belong to later
papers of the series are not included.

## Layout

- `core/` — attribute sheet, classes, solution type, XP system
- `operators/` — mode-dependent mutation and crossover
- `algorithms/` — `RPGE`
- `problems/` — ZDT test problems
- `experiments/art01_toy_figures.py` — Figs. A–C (toy landscape)
- `experiments/art01_benchmark.py` — Fig. D and the benchmark table
- `tests/` — unit tests

## Reproduce

Tested with Python 3.13, numpy 2.5, scipy 1.18 and matplotlib 3.11.

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest                                           # unit tests
python experiments/art01_toy_figures.py figs     # figA, figB, figC
python experiments/art01_benchmark.py figs       # figD, tab_benchmark.tex
```

All runs are seeded, so repeated runs give the same figures and table.

## Citation

See `CITATION.cff`. Archived versions on Zenodo carry a DOI.

## License

MIT, see `LICENSE`.
