"""Art01 illustrative benchmark: RPGE vs canonical baselines on 2D toys.

Three landscapes (toy basin+ripples, Sphere-2D, Rastrigin-2D), three
algorithms (RPGE default configuration, canonical Differential Evolution via
SciPy, uniform Random Search), 30 independent runs each, budget 3000 NFE.
Outputs a convergence figure and a LaTeX table fragment (NFE-to-target and
final quality, median [IQR]) into the given output directory.

This is an ILLUSTRATIVE benchmark at default settings: the tuned, full
battery belongs to the companion experimental paper.

Usage:
    python experiments/art01_benchmark.py [output_dir]
"""

import random
import sys
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import differential_evolution

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from algorithms.rpge import RPGE  # noqa: E402

RUNS = 30
BUDGET = 3000
POP_SIZE = 30
# Toy landscape shared with experiments/art01_toy_figures.py: the raw bowl plus
# ripples has its minimum at -1.703018494946, and the same constant shift is
# applied here so that the objective is positive on the domain and the targets
# below can be read as optimality gaps.
TOY_SHIFT = 2.0
# Optimum of each landscape; the gap is best - OPTIMA[land], so for sphere and
# rastrigin (optimum 0) the gap coincides with the objective.
OPTIMA = {"toy": -1.703018494946 + TOY_SHIFT, "sphere": 0.0, "rastrigin": 0.0}
# Targets are optimality gaps, not raw objectives.
TARGETS = {"toy": 1e-2, "sphere": 1e-6, "rastrigin": 1e-1}
# Floor of the log axis of Fig. D: only there so that a zero gap stays plottable.
GAP_FLOOR = 1e-8
BOUNDS = [(-5.0, 5.0), (-5.0, 5.0)]


def make_landscapes():
    def toy(x):
        return ((x[0] - 2.0) ** 2 + (x[1] - 3.0) ** 2
                + 2 * np.sin(3 * x[0]) * np.sin(3 * x[1]) + TOY_SHIFT)

    def sphere(x):
        return float(np.sum(x**2))

    def rastrigin(x):
        A = 10.0
        return A * 2 + np.sum(x**2 - A * np.cos(2 * np.pi * x))

    return {"toy": toy, "sphere": sphere, "rastrigin": rastrigin}


class DuckProblem:
    """RPGE-facing wrapper around a plain function."""

    def __init__(self, fn, bounds):
        self.fn = fn
        self.nvars = len(bounds)
        self.nobjs = 1
        self.nconstrs = 0
        self.types = list(bounds)

    def evaluate(self, solution):
        solution.objectives = [self.fn(list(solution.variables))]
        solution.constraint_violation = 0.0
        solution.evaluated = True


class CountingFn:
    """Wrap a function with an evaluation counter and best-so-far tracking."""

    def __init__(self, fn):
        self.fn = fn
        self.nfe = 0
        self.best = float("inf")
        self.trajectory = []

    def __call__(self, x):
        self.nfe += 1
        v = self.fn(np.asarray(x))
        if v < self.best:
            self.best = v
        self.trajectory.append((self.nfe, self.best))
        return v


def run_rpge(fn, rng_seed):
    # RPGSolution and the operators draw from the global ``random`` module, so
    # it must be seeded per run as well: without this the RPGE rows of the
    # table change on every process (the stream leaked across runs), and
    # "same seeds" would not mean anything.
    random.seed(rng_seed)
    np.random.seed(rng_seed)
    counter = CountingFn(fn)
    problem = DuckProblem(counter, BOUNDS)
    algo = RPGE(problem, population_size=POP_SIZE, max_generations=BUDGET // POP_SIZE)
    algo.initialize_population()
    for _ in range(BUDGET // POP_SIZE):
        if counter.nfe >= BUDGET:
            break  # fair NFE cap: lucky mode spends extra evaluations
        algo.evolve_generation()
    return counter.trajectory, counter.best


def run_de(fn, rng_seed):
    counter = CountingFn(fn)
    result = differential_evolution(
        counter,
        BOUNDS,
        maxiter=BUDGET // (POP_SIZE * 2) + 1,
        popsize=POP_SIZE // 2,
        tol=0.0,
        mutation=(0.5, 1.0),
        recombination=0.7,
        polish=False,
        init="latinhypercube",
        seed=rng_seed,
    )
    return counter.trajectory, counter.best


def run_de_layered(fn, rng_seed, use_layer=True):
    """Hand-rolled DE/rand/1/bin (NP=30, 100 generations, greedy survival).

    use_layer=False: vanilla DE with classic constants F=0.5, CR=0.7.
    use_layer=True:  RPG-DE — the layer of S3 over the SAME base: each
    individual's F_i = 0.1 + 0.9*mu(a_STR) and CR_i = 0.1 + 0.9*mu(a_WIS)
    come from its evolving attribute sheet. Improvement events credit the
    surviving individual with the full G (in greedy survival the parent
    slot and the survivor coincide, so the D2->C mentorship split
    collapses to a single recipient; it is instantiated in
    crossover-based bases). Level-ups redistribute R=5 unit points
    uniformly at random, clamped to [20,100]. Same base, same NFE per
    generation: the comparison isolates the layer.
    """
    rng = np.random.default_rng(rng_seed)
    counter = CountingFn(fn)
    lo = np.array([b[0] for b in BOUNDS])
    hi = np.array([b[1] for b in BOUNDS])

    pop = rng.uniform(lo, hi, size=(POP_SIZE, len(BOUNDS)))
    fit = np.array([counter(x) for x in pop])
    attrs = rng.uniform(20.0, 80.0, size=(POP_SIZE, 5))
    exp_pts = np.zeros(POP_SIZE)
    levels = np.ones(POP_SIZE, dtype=int)

    for _ in range(BUDGET // POP_SIZE - 1):
        if use_layer:
            mu = (attrs - 20.0) / 80.0
            F = 0.1 + 0.9 * mu[:, 0]
            CR = 0.1 + 0.9 * mu[:, 1]
        else:
            F = np.full(POP_SIZE, 0.5)
            CR = np.full(POP_SIZE, 0.7)

        for i in range(POP_SIZE):
            choices = [j for j in range(POP_SIZE) if j != i]
            r1, r2, r3 = rng.choice(choices, size=3, replace=False)
            mutant = pop[r1] + F[i] * (pop[r2] - pop[r3])
            mutant = np.clip(mutant, lo, hi)
            cross = rng.random(len(BOUNDS)) < CR[i]
            cross[rng.integers(len(BOUNDS))] = True
            trial = np.where(cross, mutant, pop[i])

            f_trial = counter(trial)
            if f_trial < fit[i]:
                f_old = fit[i]
                pop[i] = trial
                fit[i] = f_trial
                if use_layer:
                    rho_imp = min((f_old - f_trial) / max(abs(f_old), 1e-12), 1.0)
                    G = int(30 * (1 + rho_imp))
                    exp_pts[i] += G
                    while exp_pts[i] >= 100 * levels[i]:
                        exp_pts[i] -= 100 * levels[i]
                        levels[i] += 1
                        increments = np.bincount(
                            rng.integers(0, 5, size=5), minlength=5
                        )
                        attrs[i] = np.minimum(100.0, attrs[i] + increments)
    return counter.trajectory, counter.best


def run_random(fn, rng_seed):
    rng = np.random.default_rng(rng_seed)
    counter = CountingFn(fn)
    for _ in range(BUDGET):
        counter(rng.uniform(BOUNDS[0][0], BOUNDS[0][1], size=2))
    return counter.trajectory, counter.best


def best_at_or_before(trajectory, nfe_cap):
    """Best-so-far value at the largest recorded nfe <= nfe_cap."""
    value = float("inf")
    for nfe, best in trajectory:
        if nfe > nfe_cap:
            break
        value = best
    return value


def nfe_to_target(trajectory, target, budget=BUDGET):
    for nfe, best in trajectory:
        if best <= target:
            return nfe
    return None


def median_iqr(values):
    values = sorted(values)
    n = len(values)
    med = values[n // 2]
    q1 = values[max(0, n // 4)]
    q3 = values[min(n - 1, (3 * n) // 4)]
    return med, q1, q3


def main():
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("figs")
    out_dir.mkdir(parents=True, exist_ok=True)

    landscapes = make_landscapes()
    algorithms = {
        "RPGE (core)": run_rpge,
        "RPG-DE": lambda fn, seed: run_de_layered(fn, seed, use_layer=True),
        "DE (plain)": lambda fn, seed: run_de_layered(fn, seed, use_layer=False),
        "DE (scipy)": run_de,
        "Random": run_random,
    }
    colors = {
        "RPGE (core)": "#D64545",
        "RPG-DE": "#7B5EA7",
        "DE (plain)": "#3C6EB4",
        "DE (scipy)": "#3C6EB4",
        "Random": "#888888",
    }
    styles = {
        "RPGE (core)": "--",
        "RPG-DE": "-",
        "DE (plain)": "-",
        "DE (scipy)": "--",
        "Random": ":",
    }

    summary = {}
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.2))

    for ax, (land, fn) in zip(axes, landscapes.items()):
        curves = {}
        finals = {}
        targets = {}
        for algo_name, runner in algorithms.items():
            trajs, finals_list, target_list = [], [], []
            for seed in range(RUNS):
                traj, best = runner(fn, seed * 100 + 7)
                trajs.append(traj)
                finals_list.append(best)
                nfe_t = nfe_to_target(traj, OPTIMA[land] + TARGETS[land])
                if nfe_t is not None:
                    target_list.append(nfe_t)
            curves[algo_name] = trajs
            finals[algo_name] = finals_list
            targets[algo_name] = target_list

        # median convergence curves on the common NFE grid
        grid = np.unique(np.linspace(30, BUDGET, 60).astype(int))
        for algo_name in algorithms:
            vals = []
            for nfe_pt in grid:
                vals.append([best_at_or_before(t, nfe_pt) for t in curves[algo_name]])
            med = np.median(vals, axis=1)
            q1 = np.percentile(vals, 25, axis=1)
            q3 = np.percentile(vals, 75, axis=1)
            color = colors[algo_name]
            # Optimalidad: la brecha best - optimo, con suelo solo para los ceros.
            gap_med = med - OPTIMA[land]
            gap_q1 = q1 - OPTIMA[land]
            gap_q3 = q3 - OPTIMA[land]
            ax.plot(grid, np.maximum(gap_med, GAP_FLOOR), color=color, lw=1.6,
                    ls=styles[algo_name], label=algo_name)
            ax.fill_between(grid, np.maximum(gap_q1, GAP_FLOOR),
                            np.maximum(gap_q3, GAP_FLOOR),
                            color=color, alpha=0.10, lw=0)

        ax.set_yscale("log")
        ax.set_title(land, fontsize=10)
        ax.set_xlabel("NFE")
        if ax is axes[0]:
            ax.set_ylabel("optimality gap (median, IQR)")
        ax.legend(fontsize=7, frameon=False)

        summary[land] = {
            "target": TARGETS[land],
            "nfe_to_target": {
                a: median_iqr(targets[a]) if targets[a] else None
                for a in algorithms
            },
            "final": {a: median_iqr(finals[a]) for a in algorithms},
            "success_rate": {
                a: f"{len(targets[a])}/{RUNS}" for a in algorithms
            },
        }

    fig.tight_layout()
    fig.savefig(out_dir / "figD_benchmark.pdf")
    plt.close(fig)

    # --- LaTeX table fragment ---------------------------------------------
    rows = []
    for land, s in summary.items():
        tgt = s["target"]
        tgt_str = f"$10^{{{int(np.log10(tgt))}}}$"
        for algo in algorithms:
            nfe_s = s["nfe_to_target"][algo]
            fin = s["final"][algo]
            nfe_cell = (
                f"{nfe_s[0]} [{nfe_s[1]} to {nfe_s[2]}]" if nfe_s else
                f">$\\textstyle{BUDGET}$"
            )
            rows.append(
                f"{land} & {algo} & {nfe_cell} & "
                f"{fin[0]:.3g} [{fin[1]:.3g}, {fin[2]:.3g}] & "
                f"{s['success_rate'][algo]} \\\\"
            )
    table = (
        "\\begin{tabular}{llrrl}\n\\hline\n"
        "Landscape & Algorithm & NFE to target & Final best (med [IQR]) & Success \\\\\n"
        "\\hline\n" + "\n".join(rows) + "\n\\hline\n\\end{tabular}\n"
    )
    (out_dir / "tab_benchmark.tex").write_text(table)

    print(f"outputs written to {out_dir.resolve()}")
    for land, s in summary.items():
        print(land, "target", s["target"], "success", s["success_rate"])


if __name__ == "__main__":
    main()
