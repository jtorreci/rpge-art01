"""
RPG-Based Evolutionary Algorithm (RPGE).

Algoritmo evolutivo que usa atributos RPG para adaptar operadores
y gestionar la evolución de la población.
"""
import random
from typing import List, Tuple, Optional
from core.rpg_solution import RPGSolution
from core.xp_system import (
    calculate_dominance_xp,
    calculate_improvement_xp,
    calculate_survival_xp,
    calculate_pareto_front_xp
)
from operators.rpg_mutation import rpg_mutate


class RPGE:
    """
    RPG-Based Evolutionary Algorithm.

    Attributes
    ----------
    problem : object
        Problema de optimización
    population_size : int
        Tamaño de la población
    max_generations : int
        Número máximo de generaciones
    population : List[RPGSolution]
        Población actual
    pareto_front : List[RPGSolution]
        Frente de Pareto actual

    Examples
    --------
    >>> from problems.muro_base import Muro
    >>> problem = create_muro_problem()
    >>> rpge = RPGE(problem, population_size=100, max_generations=250)
    >>> result = rpge.run()
    >>> print(f"Soluciones Pareto: {len(result['pareto_front'])}")
    """

    def __init__(
        self,
        problem,
        population_size: int = 100,
        max_generations: int = 250,
        endurance_mode: str = 'variation'
    ):
        """
        Inicializar algoritmo RPGE.

        Parameters
        ----------
        problem : object
            Problema de optimización con método evaluate()
        population_size : int, optional
            Tamaño de población (default: 100)
        max_generations : int, optional
            Generaciones máximas (default: 250)
        endurance_mode : str, optional
            "variation" (default, formalismo de tesis): la selección es
            fitness-pura (solo valor objetivo; sin END ni combat_power) y
            END actúa dentro de la VARIACIÓN como estabilidad conductual
            (tanque estable, ver operators/rpg_mutation.py).
            "selection" (legacy pre-formalismo): preserva el comportamiento
            enviado originalmente, con endurance*0.1 + combat_power*0.01 en
            el score de selección.

        Raises
        ------
        ValueError
            Si endurance_mode no es "variation" ni "selection"
        """
        if endurance_mode not in ('variation', 'selection'):
            raise ValueError(
                f"endurance_mode debe ser 'variation' o 'selection', "
                f"no {endurance_mode!r}"
            )

        self.problem = problem
        self.population_size = population_size
        self.max_generations = max_generations
        self.endurance_mode = endurance_mode

        self.population: List[RPGSolution] = []
        self.pareto_front: List[RPGSolution] = []

        self.generation = 0

        # Presión de selección (proxy: generaciones de estancamiento
        # normalizadas) para el amortiguado de END en variación
        self.STAGNATION_WINDOW = 10
        self._stagnation_count = 0
        self._best_cost: Optional[float] = None

    def initialize_population(self) -> None:
        """Crear población inicial aleatoria."""
        self.population = []

        for _ in range(self.population_size):
            sol = RPGSolution(self.problem)

            # Inicializar variables aleatorias en rangos válidos
            sol.variables = [
                random.uniform(*self.problem.types[i])
                for i in range(self.problem.nvars)
            ]

            # Evaluar
            self.problem.evaluate(sol)

            self.population.append(sol)

    def update_pareto_front(self) -> None:
        """Actualizar frente de Pareto con población actual."""
        # Combinar población y frente actual
        combined = self.population + self.pareto_front

        # Filtrar dominados
        non_dominated = []

        for sol in combined:
            is_dominated = False

            for other in combined:
                if sol is other:
                    continue

                # Verificar dominancia (minimización de ambos objetivos)
                if self._dominates(other, sol):
                    is_dominated = True
                    break

            if not is_dominated:
                non_dominated.append(sol)

        # Actualizar frente
        self.pareto_front = non_dominated

        # Dar XP a soluciones en frente
        for sol in self.pareto_front:
            if sol in self.population:
                sol.gain_xp(calculate_pareto_front_xp())

    def _dominates(self, sol1: RPGSolution, sol2: RPGSolution) -> bool:
        """
        Verificar si sol1 domina a sol2 (minimización).

        Parameters
        ----------
        sol1 : RPGSolution
            Primera solución
        sol2 : RPGSolution
            Segunda solución

        Returns
        -------
        bool
            True si sol1 domina a sol2
        """
        if not sol1.objectives or not sol2.objectives:
            return False

        # sol1 domina si es mejor o igual en todos, y mejor en al menos uno
        better_in_all = all(sol1.objectives[i] <= sol2.objectives[i]
                           for i in range(len(sol1.objectives)))

        better_in_one = any(sol1.objectives[i] < sol2.objectives[i]
                           for i in range(len(sol1.objectives)))

        return better_in_all and better_in_one

    def tournament_selection(self, tournament_size: int = 2) -> RPGSolution:
        """
        Selección por torneo.

        En modo "variation" (default, formalismo) el score es fitness-puro:
        solo el valor objetivo, sin bonus de Endurance ni combat_power.
        En modo "selection" (legacy) se preserva el score histórico:
        objetivo - combat_power*0.01 - endurance*0.1.

        Parameters
        ----------
        tournament_size : int, optional
            Tamaño del torneo (default: 2)

        Returns
        -------
        RPGSolution
            Solución ganadora
        """
        # Elegir participantes aleatorios
        participants = random.sample(self.population, tournament_size)

        # Desempate determinista ante empate exacto de fitness: gana la
        # solución más antigua en la población. Neutral en calidad (no usa
        # atributos RPG: selección fitness-pura, D1->B) y elimina la
        # ambigüedad del orden aleatorio de muestreo ante empates.
        pop_index = {id(sol): idx for idx, sol in enumerate(self.population)}
        participants.sort(key=lambda s: pop_index[id(s)])

        # Calcular score según el modo de END
        def selection_score(sol: RPGSolution) -> float:
            # Normalizar objetivo principal (coste)
            obj_score = sol.objectives[0] if sol.objectives else 1e6

            if self.endurance_mode == 'variation':
                # Formalismo: selección fitness-pura
                return obj_score

            # Legacy: bonus por poder de combate (favorece veteranas)
            combat_power = sol.get_combat_power()
            power_bonus = combat_power * 0.01

            # Legacy: bonus por endurance (resistencia a eliminación)
            endurance_bonus = sol.endurance * 0.1

            return obj_score - power_bonus - endurance_bonus

        # Elegir mejor (menor score)
        winner = min(participants, key=selection_score)

        # Dar XP por supervivencia
        winner.gain_xp(int(calculate_survival_xp(1)))

        return winner

    def _current_pressure(self) -> float:
        """
        Presión de selección normalizada en [0, 1] para el modo "variation".

        Proxy documentado: generaciones consecutivas sin mejora del mejor
        coste, normalizadas por STAGNATION_WINDOW.

        Returns
        -------
        float
            Presión en [0, 1]
        """
        return min(self._stagnation_count / self.STAGNATION_WINDOW, 1.0)

    def _update_stagnation_tracking(self) -> None:
        """
        Actualizar el contador de estancamiento tras la selección ambiental.

        Si el mejor coste de la población mejoró, se reinicia el contador;
        en caso contrario se incrementa.
        """
        best = min((s.objectives[0] for s in self.population if s.objectives),
                   default=None)

        if best is None:
            return

        if self._best_cost is None or best < self._best_cost:
            self._stagnation_count = 0
        else:
            self._stagnation_count += 1

        self._best_cost = best

    def evolve_generation(self) -> None:
        """Evolucionar una generación."""
        offspring_pop = []

        # Presión de selección para el amortiguado de END en variación
        pressure = self._current_pressure()

        # Eventos de mentoria (D2->C): como máximo un evento de mejora y
        # uno de dominancia por padre y generación. El primer offspring
        # cualificado dispara el evento y su XP total se reparte 50/50;
        # la supervivencia sigue pagándose por torneo ganado.
        improvement_paid = set()
        dominance_paid = set()

        # Generar offspring mediante mutación
        for _ in range(self.population_size):
            # Seleccionar padre
            parent = self.tournament_selection()

            # Mutar usando operadores RPG
            offspring = rpg_mutate(parent, self.problem, self.pareto_front,
                                   pressure=pressure,
                                   endurance_mode=self.endurance_mode)

            # El offspring nace con XP 0: la experiencia se gana, no se
            # hereda del padre a traves de copy() (reparto de mentoria
            # 50/50, decision D2->C)
            offspring.reset_xp()

            # Evaluar
            self.problem.evaluate(offspring)

            # Dar XP si hay mejora (reparto 50/50 padre/offspring, D2->C)
            if offspring.objectives and parent.objectives:
                if (offspring.objectives[0] < parent.objectives[0]
                        and id(parent) not in improvement_paid):
                    improvement_ratio = (parent.objectives[0] - offspring.objectives[0]) / parent.objectives[0]
                    total_xp = int(calculate_improvement_xp(improvement_ratio))
                    parent_share = total_xp // 2
                    offspring_share = total_xp - parent_share
                    parent.gain_xp(parent_share)
                    offspring.gain_xp(offspring_share)
                    improvement_paid.add(id(parent))

            # Verificar dominancia (reparto 50/50 padre/offspring, D2->C)
            if self._dominates(offspring, parent) and id(parent) not in dominance_paid:
                total_xp = calculate_dominance_xp()
                parent_share = total_xp // 2
                offspring_share = total_xp - parent_share
                parent.gain_xp(parent_share)
                offspring.gain_xp(offspring_share)
                dominance_paid.add(id(parent))

            offspring_pop.append(offspring)

        # Combinar población actual y offspring
        combined = self.population + offspring_pop

        # Seleccionar mejores para siguiente generación (NSGA-II style)
        self.population = self._environmental_selection(combined)

        # Incrementar edad de supervivientes
        for sol in self.population:
            sol.increment_age()

        # Actualizar presión de selección (estancamiento)
        self._update_stagnation_tracking()

    def _environmental_selection(self, combined: List[RPGSolution]) -> List[RPGSolution]:
        """
        Selección ambiental: elegir mejores soluciones.

        Parameters
        ----------
        combined : List[RPGSolution]
            Población combinada (padres + offspring)

        Returns
        -------
        List[RPGSolution]
            Mejores population_size soluciones
        """
        # Ordenar por primer objetivo (coste) y tomar los mejores
        sorted_pop = sorted(combined, key=lambda s: s.objectives[0] if s.objectives else 1e6)

        return sorted_pop[:self.population_size]

    def run(self) -> dict:
        """
        Ejecutar algoritmo RPGE.

        Returns
        -------
        dict
            Resultados con frente de Pareto y estadísticas
        """
        import time

        start_time = time.time()

        print(f"RPGE: Inicializando población de {self.population_size} soluciones...")
        self.initialize_population()

        print(f"RPGE: Evolucionando por {self.max_generations} generaciones...")

        for gen in range(self.max_generations):
            self.generation = gen

            # Evolucionar
            self.evolve_generation()

            # Actualizar frente de Pareto
            self.update_pareto_front()

            # Log progreso
            if (gen + 1) % 50 == 0:
                best_cost = min(s.objectives[0] for s in self.population if s.objectives)
                avg_level = sum(s.level for s in self.population) / len(self.population)
                print(f"  Gen {gen+1}/{self.max_generations}: "
                      f"Mejor coste={best_cost:.2f}, "
                      f"Frente Pareto={len(self.pareto_front)}, "
                      f"Nivel promedio={avg_level:.1f}")

        elapsed_time = time.time() - start_time

        print(f"RPGE: Finalizado. Frente de Pareto: {len(self.pareto_front)} soluciones")

        return {
            'pareto_front': self.pareto_front,
            'population': self.population,
            'generations': self.max_generations,
            'elapsed_time': elapsed_time,
            'algorithm': 'RPGE'
        }
