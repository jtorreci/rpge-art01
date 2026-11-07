"""Art01 toy figures: attribute trajectories, per-seed class census, IP vs performance.

Generates the illustrative figures of thesis paper #1 (RPG formalism) from a
small 2D toy landscape. Writes vector PDFs to the directory given as the
first CLI argument (default: ./figs).

Usage:
    python experiments/art01_toy_figures.py [output_dir]
"""

import math
import random
import sys
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from algorithms.rpge import RPGE  # noqa: E402
from core.rpg_attributes import (  # noqa: E402
    get_dexterity_precision,
    get_mutation_strength_modifier,
)
from core.rpg_classes import assign_rpg_class  # noqa: E402
from operators.rpg_mutation import endurance_damping_factor, rpg_mutate  # noqa: E402

# Channel accent palette (same as the project's visual identity).
CHANNELS = ["STR", "WIS", "END", "DEX", "LCK"]
CHANNEL_ATTRS = ["strength", "wisdom", "endurance", "dexterity", "luck"]
CHANNEL_COLORS = {
    "STR": "#D64545",
    "WIS": "#7B5EA7",
    "END": "#5E8C6A",
    "DEX": "#E0A83C",
    "LCK": "#3CB8C4",
}
CLASS_COLORS = {
    "warrior": "#D64545",   # STR
    "monk": "#5E8C6A",      # END
    "rogue": "#E0A83C",     # DEX
    "scout": "#3CB8C4",     # LCK
    "paladin": "#7B5EA7",   # WIS
}

GENERATIONS = 300
POP_SIZE = 30
# Cap of the empirical IP estimation: enough draws that every coordinate keeps
# at least ~30 moved samples once the coordinate gate (rate r ~ 0.3-0.5) has
# been taken into account.
IP_SAMPLES = 120
# Generations at which the closed-form IP and the estimate are printed per
# individual and compared (block A, item S4).
IPCHECK_GENS = (1, 50, 150, 300)
# Fig. B runs its own seeds: the per-seed census must not consume the random
# stream of the trajectory run (nor the other way round).
FIG_B_SEEDS = list(range(10))

# Constant added to the Toy2D objective (block A, S3). The raw landscape has
# its minimum at -1.703018494946; with this shift the objective is positive on
# [0,10]^2, which is what the relative-improvement reward of the paper needs
# (rho = (f_P - f_O)/f_P in [0,1] requires f > 0). A constant shift changes
# neither the selection order nor the variation operators.
TOY_SHIFT = 2.0

# Global minimum of the shifted Toy2D landscape, F_STAR = -1.703018494946 +
# TOY_SHIFT, located at (1.6140859107, 2.6565635648). Method: best cell of a
# dense 4001^2 grid on [0,10]^2 refined with a bounded L-BFGS-B local minimizer
# (ftol/gtol 1e-15/1e-12); refining the 20 best grid cells reproduces the same
# value to 4e-16 and the gradient norm at the optimum is 3e-13. Fig. C plots
# the optimality gap best_so_far - F_STAR.
F_STAR = -1.703018494946 + TOY_SHIFT
# Floor for the log axis: keeps at 1e-8 a gap that is exactly zero, which a
# logarithmic scale cannot represent. With the refined F_STAR the gap is
# strictly positive throughout the run, so the floor does not bind.
GAP_FLOOR = 1e-8


class Toy2D:
    """Single-objective 2D landscape: bowl + gentle ripples, shifted positive.

    The raw landscape (x-2)^2 + (y-3)^2 + 2 sin(3x) sin(3y) has its minimum at
    -1.703018494946; ``TOY_SHIFT`` adds a constant so the objective is positive
    on the domain and the relative-improvement reward of the formalism stays a
    coherent measure of improvement.
    """

    nvars = 2
    nobjs = 1
    nconstrs = 0
    types = [(0.0, 10.0), (0.0, 10.0)]

    def evaluate(self, solution):
        x, y = solution.variables
        solution.objectives = [
            (x - 2.0) ** 2 + (y - 3.0) ** 2
            + 2.0 * np.sin(3 * x) * np.sin(3 * y) + TOY_SHIFT
        ]
        solution.constraint_violation = 0.0
        solution.evaluated = True


def empirical_ip(individual, problem, pareto_front, pressure, samples=IP_SAMPLES):
    """Estimate the predictability index from sampled displacements.

    Per-coordinate step std estimates the Gaussian-equivalent width
    W(K) = sqrt(2*pi*e) * sigma; IP = 1 - W / (2 * delta_world) with the
    world reach delta_w = 0.30 * mean(range).

    A coordinate stays at zero displacement with probability 1 - r (the world
    gate), so its std is taken only over the draws in which it actually moved:
    mixing the atom at zero into the std would bias sigma by about sqrt(r)
    (block A, item S1).
    """
    draws = []
    for _ in range(samples):
        offspring = rpg_mutate(
            individual,
            problem,
            pareto_front,
            pressure=pressure,
            endurance_mode="variation",
        )
        draws.append(
            (offspring.variables[0] - individual.variables[0],
             offspring.variables[1] - individual.variables[1])
        )
    arr = np.array(draws)
    sigmas = []
    for k in range(arr.shape[1]):
        moved = arr[:, k][arr[:, k] != 0.0]
        if moved.size >= 2:
            sigmas.append(float(moved.std()))
    if not sigmas:
        return 0.0
    sigma_hat = float(np.mean(sigmas))
    reach = 0.3 * 10.0  # delta_w = 0.30 * mean(range) = 3.0
    width = np.sqrt(2 * np.pi * np.e) * sigma_hat
    return max(0.0, 1.0 - width / (2.0 * reach))


def closed_form_ip(individual, pareto_front, pressure):
    """Closed-form IP of Prop. "Range, closed forms, and invariances" (i).

    Uses the mode parameters of Table 1 computed from the individual's sheet
    through the code's own modifier functions. Returns (ip, mode); ip is None
    for the modes without a Gaussian closed form (guided, lucky), so callers
    average over the eligible individuals only.
    """
    sheet = {a: getattr(individual, a) for a in CHANNEL_ATTRS}
    dominant = individual.get_dominant_attribute()
    span = 10.0                     # coordinate range rho of the toy landscape
    reach = 0.3 * span              # world reach delta_w
    if dominant == "dexterity":
        sigma = span * 0.1 * get_dexterity_precision(sheet["dexterity"]) / 3.0
        mode = "precise"
    elif dominant == "endurance":
        damping = endurance_damping_factor(sheet["endurance"], pressure)
        sigma = (span
                 * (0.05 + 0.25 * get_mutation_strength_modifier(sheet["strength"]))
                 * damping / 3.0)
        mode = "stable"
    elif dominant == "wisdom":
        if pareto_front and len(pareto_front) > 0 and sheet["wisdom"] > 50:
            return None, "guided"
        sigma = span * (0.05 + 0.25 * get_mutation_strength_modifier(sheet["strength"])) / 3.0
        mode = "aggressive-fallback"
    elif dominant == "luck":
        return None, "lucky"
    else:
        sigma = span * (0.05 + 0.25 * get_mutation_strength_modifier(sheet["strength"])) / 3.0
        mode = "aggressive"
    return 1.0 - math.sqrt(2 * math.pi * math.e) * sigma / (2 * reach), mode


def prune_archive(algo):
    """Reduce the Pareto archive to one representative of the best objective.

    On a single-objective landscape the non-dominated set is the set of
    minimizers, but ``RPGE.update_pareto_front`` keeps every tie, so on a
    population of clones the archive grows without bound and its O(n^2)
    dominance filter becomes the bottleneck of the run. Keeping one
    representative of the best objective value preserves the archive's
    meaning for this problem and keeps the WIS-guided mode fed.
    """
    if not algo.pareto_front:
        return
    best = min(s.objectives[0] for s in algo.pareto_front if s.objectives)
    algo.pareto_front = [next(s for s in algo.pareto_front
                              if s.objectives and s.objectives[0] == best)]


def per_seed_class_census(problem):
    """Class census per generation for ten independent seeds.

    Reproduces the toy configuration (N = 30, 300 generations, default
    ``endurance_mode``) without the empirical IP estimation, which consumes
    the random stream and is not part of the census.

    Returns
    -------
    Dict[int, Dict[str, List[int]]]
        Per seed, the number of individuals of each class along the run
        (generations 1..GENERATIONS), in canonical class order.
    """
    censuses = {}
    for seed in FIG_B_SEEDS:
        random.seed(seed)
        np.random.seed(seed)
        algo = RPGE(problem, population_size=POP_SIZE, max_generations=GENERATIONS)
        algo.initialize_population()
        counts = {c: [] for c in CLASS_COLORS}
        for _ in range(GENERATIONS):
            algo.evolve_generation()
            # Como en RPGE.run() (algorithms/rpge.py:370-377): sin esta llamada
            # el archivo queda vacío y el modo guiado nunca puede disparar.
            algo.update_pareto_front()
            prune_archive(algo)
            tally = {c: 0 for c in CLASS_COLORS}
            for sol in algo.population:
                sheet = {a: getattr(sol, a) for a in CHANNEL_ATTRS}
                tally[assign_rpg_class(sheet)] += 1
            for c in CLASS_COLORS:
                counts[c].append(tally[c])
        censuses[seed] = counts
    return censuses


def main():
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("figs")
    out_dir.mkdir(parents=True, exist_ok=True)

    problem = Toy2D()
    # Instrumentación de solo conteo (no altera el flujo aleatorio): cuántas
    # veces el despacho de operadores elige el modo guiado, es decir WIS
    # dominante con archivo no vacío y WIS > 50 (block A, item S2).
    import algorithms.rpge as _rpge
    _original_mutate = _rpge.rpg_mutate
    guided = {"n": 0, "total": 0}

    def _counting_mutate(parent, problem, pareto_front=None, pressure=0.0,
                         endurance_mode="variation", **kw):
        guided["total"] += 1
        if (parent.get_dominant_attribute() == "wisdom"
                and pareto_front and len(pareto_front) > 0
                and parent.wisdom > 50):
            guided["n"] += 1
        return _original_mutate(parent, problem, pareto_front,
                                pressure=pressure,
                                endurance_mode=endurance_mode, **kw)

    _rpge.rpg_mutate = _counting_mutate
    # La corrida de trayectoria va sembrada: sus figuras (A y C) deben ser
    # reproducibles y coincidir con el panel "seed 0" del censo de Fig. B.
    random.seed(0)
    np.random.seed(0)
    algo = RPGE(problem, population_size=POP_SIZE, max_generations=GENERATIONS)
    algo.initialize_population()

    attr_means = {c: [] for c in CHANNELS}
    attr_lo = {c: [] for c in CHANNELS}
    attr_hi = {c: [] for c in CHANNELS}
    mean_ip = []
    best_so_far = []

    best = float("inf")
    for gen in range(GENERATIONS):
        algo.evolve_generation()
        # Como en RPGE.run() (algorithms/rpge.py:370-377): el archivo debe
        # actualizarse para que el modo guiado pueda seleccionarse.
        algo.update_pareto_front()
        prune_archive(algo)
        pressure = algo._current_pressure()

        attrs = np.array(
            [[getattr(s, a) for a in CHANNEL_ATTRS] for s in algo.population]
        )
        for k, c in enumerate(CHANNELS):
            attr_means[c].append(attrs[:, k].mean())
            attr_lo[c].append(np.percentile(attrs[:, k], 10))
            attr_hi[c].append(np.percentile(attrs[:, k], 90))

        # La estimación empírica de IP muta copias del individuo y consume el
        # flujo aleatorio global. Se guarda y restaura ese estado para que la
        # trayectoria evolucionada sea exactamente la de la corrida no
        # observada (semilla 0); las mutaciones de la estimación son
        # instrumentación y NO cuentan como NFE del algoritmo.
        py_state = random.getstate()
        np_state = np.random.get_state()
        ips = []
        for s in algo.population:
            ips.append(empirical_ip(s, problem, algo.pareto_front, pressure))
        random.setstate(py_state)
        np.random.set_state(np_state)
        mean_ip.append(float(np.mean(ips)))

        # Comparación forma cerrada vs estimador (block A, item S4).
        if (gen + 1) in IPCHECK_GENS:
            pairs = []
            for idx, (s, est) in enumerate(zip(algo.population, ips)):
                ip_c, mode = closed_form_ip(s, algo.pareto_front, pressure)
                shown = "n/a" if ip_c is None else f"{ip_c:.4f}"
                print(f"  IPDETAIL gen={gen + 1} i={idx:02d} mode={mode} "
                      f"closed={shown} estimate={est:.4f}")
                if ip_c is not None:
                    pairs.append((ip_c, est))
            if pairs:
                c_mean = sum(p[0] for p in pairs) / len(pairs)
                e_mean = sum(p[1] for p in pairs) / len(pairs)
                print(f"IPCHECK gen={gen + 1} closed={c_mean:.4f} "
                      f"estimate={e_mean:.4f}")

        gen_best = min(s.objectives[0] for s in algo.population)
        best = min(best, gen_best)
        best_so_far.append(best)

    gens = np.arange(1, GENERATIONS + 1)
    _rpge.rpg_mutate = _original_mutate
    print(f"guided-mode dispatches in the trajectory run: {guided['n']} "
          f"of {guided['total']} mutations")

    # --- Fig A: attribute trajectories (guild means + 10-90% band) --------
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    for c in CHANNELS:
        ax.plot(gens, attr_means[c], color=CHANNEL_COLORS[c], lw=1.8, label=c)
        ax.fill_between(gens, attr_lo[c], attr_hi[c], color=CHANNEL_COLORS[c],
                        alpha=0.12, lw=0)
    ax.set_xlabel("generation")
    ax.set_ylabel("attribute value (population mean)")
    ax.set_xlim(1, GENERATIONS)
    ax.set_ylim(15, 105)
    ax.legend(ncol=5, fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(out_dir / "figA_trajectories.pdf")
    plt.close(fig)

    # --- Fig B: per-seed class census (ten panels, shared legend) ---------
    censuses = per_seed_class_census(problem)
    fig, axes = plt.subplots(2, 5, figsize=(12.0, 4.4), sharex=True, sharey=True)
    for ax, seed in zip(axes.ravel(), FIG_B_SEEDS):
        counts = censuses[seed]
        ax.stackplot(gens,
                     *[counts[c] for c in CLASS_COLORS],
                     labels=list(CLASS_COLORS),
                     colors=[CLASS_COLORS[c] for c in CLASS_COLORS],
                     alpha=0.85, lw=0)
        ax.set_title(f"seed {seed}", fontsize=8)
        ax.set_xlim(1, GENERATIONS)
        ax.set_ylim(0, POP_SIZE)
        ax.tick_params(labelsize=7)
    for ax in axes[:, 0]:
        ax.set_ylabel("individuals", fontsize=8)
    for ax in axes[-1, :]:
        ax.set_xlabel("generation", fontsize=8)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=len(CLASS_COLORS), fontsize=8,
               frameon=False, loc="lower center")
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(out_dir / "figB_classes.pdf")
    plt.close(fig)

    # --- Fig C: predictability vs optimality gap --------------------------
    # El objetivo de Toy2D es negativo (mínimo global F_STAR), de modo que
    # sobre eje logarítmico se dibuja la brecha de optimalidad
    # best_so_far - F_STAR, con suelo GAP_FLOOR solo para los ceros.
    gap = [max(b - F_STAR, GAP_FLOOR) for b in best_so_far]
    fig, ax1 = plt.subplots(figsize=(6.4, 3.0))
    ax1.plot(gens, mean_ip, color="#333333", lw=1.8,
             label="mean IP (population)")
    ax1.set_xlabel("generation")
    ax1.set_ylabel("mean predictability IP", color="#333333")
    ax1.set_xlim(1, GENERATIONS)
    ax1.set_ylim(0, 1)
    ax2 = ax1.twinx()
    ax2.semilogy(gens, gap, color="#B0413E", lw=1.4,
                 ls="--", label="optimality gap (log)")
    ax2.set_ylabel("optimality gap (log)", color="#B0413E")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=8, frameon=False,
               loc="center right")
    fig.tight_layout()
    fig.savefig(out_dir / "figC_ip_performance.pdf")
    plt.close(fig)

    print(f"figures written to {out_dir.resolve()}")
    print(f"final best objective: {best_so_far[-1]:.4f}")
    raw_gap = [b - F_STAR for b in best_so_far]
    print(f"optimality gap (F_STAR = {F_STAR}): min = {min(raw_gap):.6e}, "
          f"final = {raw_gap[-1]:.6e}")
    for thr in (1e-1, 1e-2, 1e-3, 1e-5, 1e-6, 1e-7):
        first = next((int(g) for g, v in zip(gens, raw_gap) if v < thr), None)
        print(f"  first generation below {thr:.0e} = {first}")
    print("  improvement steps (generation, best, gap):")
    prev = None
    for g, (b, d) in enumerate(zip(best_so_far, raw_gap), start=1):
        if prev is None or b < prev - 1e-12:
            print(f"    gen {g:3d}  best={b:.6f}  gap={d:.3e}")
            prev = b
    print(f"final mean IP: {mean_ip[-1]:.3f}")
    print("final class per seed (generation 300):")
    for seed in FIG_B_SEEDS:
        final = {c: censuses[seed][c][-1] for c in CLASS_COLORS
                 if censuses[seed][c][-1]}
        print(f"  seed {seed}: {final}")
    final_counts = {c: 0 for c in CLASS_COLORS}
    for s in algo.population:
        sheet = {a: getattr(s, a) for a in CHANNEL_ATTRS}
        final_counts[assign_rpg_class(sheet)] += 1
    print("trajectory run (seed 0) final class counts: "
          f"{ {c: n for c, n in final_counts.items() if n} }")


if __name__ == "__main__":
    main()
