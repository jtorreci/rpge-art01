"""
Operadores de mutación basados en atributos RPG.

Estos operadores adaptan su comportamiento según los atributos RPG
de la solución (Strength, Dexterity, Wisdom, Luck).
"""
import random
from typing import Optional, List, Any
from core.rpg_solution import RPGSolution
from core.rpg_attributes import (
    get_mutation_strength_modifier,
    get_dexterity_precision,
    get_luck_probability_boost,
    get_endurance_stability
)


# =============================================================================
# MUTACIÓN ADAPTATIVA (basada en Strength)
# =============================================================================

def adaptive_mutation(
    parent: RPGSolution,
    problem: Any,
    mutation_rate: float = 0.3
) -> RPGSolution:
    """
    Mutación adaptativa basada en Strength.

    Parameters
    ----------
    parent : RPGSolution
        Solución padre
    problem : object
        Problema con atributos nvars y types (límites)
    mutation_rate : float, optional
        Probabilidad de mutar cada variable (default: 0.3)

    Returns
    -------
    RPGSolution
        Offspring mutado

    Notes
    -----
    - Alta Strength -> mutaciones grandes (mayor exploración)
    - Baja Strength -> mutaciones pequeñas (mayor explotación)
    - Usa modificador normalizado [0, 1] de Strength

    Examples
    --------
    >>> offspring = adaptive_mutation(parent, problem)
    >>> # Offspring tendrá cambios proporcionales a parent.strength
    """
    offspring = parent.copy()

    # Obtener modificador de fuerza
    strength_mod = get_mutation_strength_modifier(parent.strength)

    for i in range(problem.nvars):
        if random.random() < mutation_rate:
            # Obtener límites de la variable
            lower, upper = problem.types[i]
            range_size = upper - lower

            # Magnitud de mutación basada en strength
            # Strength alta = cambios hasta 30% del rango
            # Strength baja = cambios hasta 5% del rango
            max_change = range_size * (0.05 + strength_mod * 0.25)

            # Aplicar mutación gaussiana
            delta = random.gauss(0, max_change / 3)
            new_value = offspring.variables[i] + delta

            # Respetar límites
            offspring.variables[i] = max(lower, min(upper, new_value))

    offspring.evaluated = False
    return offspring


# =============================================================================
# MUTACIÓN FINA (basada en Dexterity)
# =============================================================================

def fine_tune_mutation(
    parent: RPGSolution,
    problem: Any,
    mutation_rate: float = 0.5
) -> RPGSolution:
    """
    Mutación fina basada en Dexterity.

    Parameters
    ----------
    parent : RPGSolution
        Solución padre
    problem : object
        Problema con límites de variables
    mutation_rate : float, optional
        Probabilidad de mutar cada variable (default: 0.5)

    Returns
    -------
    RPGSolution
        Offspring con ajustes finos

    Notes
    -----
    - Alta Dexterity -> cambios muy pequeños y precisos
    - Baja Dexterity -> cambios menos precisos
    - Útil para convergencia en fase final de optimización

    Examples
    --------
    >>> offspring = fine_tune_mutation(parent, problem)
    >>> # Cambios sutiles para refinar solución
    """
    offspring = parent.copy()

    # Obtener factor de precisión (menor = más preciso)
    precision_factor = get_dexterity_precision(parent.dexterity)

    for i in range(problem.nvars):
        if random.random() < mutation_rate:
            lower, upper = problem.types[i]
            range_size = upper - lower

            # Cambios muy pequeños, modulados por dexterity
            # Alta dexterity (precision_factor bajo) -> cambios ~1-2% rango
            # Baja dexterity (precision_factor alto) -> cambios ~5-10% rango
            max_change = range_size * precision_factor * 0.1

            # Mutación gaussiana fina
            delta = random.gauss(0, max_change / 3)
            new_value = offspring.variables[i] + delta

            # Respetar límites
            offspring.variables[i] = max(lower, min(upper, new_value))

    offspring.evaluated = False
    return offspring


# =============================================================================
# MUTACIÓN CON SESGO DE LUCK
# =============================================================================

def luck_based_mutation(
    parent: RPGSolution,
    problem: Any,
    mutation_rate: float = 0.3
) -> RPGSolution:
    """
    Mutación con sesgo favorable basado en Luck.

    Parameters
    ----------
    parent : RPGSolution
        Solución padre
    problem : object
        Problema de optimización
    mutation_rate : float, optional
        Probabilidad base de mutación (default: 0.3)

    Returns
    -------
    RPGSolution
        Offspring con mutaciones "afortunadas"

    Notes
    -----
    - Alta Luck -> sesgo hacia valores que históricamente funcionan mejor
    - Genera múltiples candidatos y elige el mejor
    - Simula "suerte" mediante sampling múltiple

    Examples
    --------
    >>> offspring = luck_based_mutation(parent, problem)
    >>> # Offspring tiene mayor probabilidad de ser mejora
    """
    # Obtener boost de probabilidad por suerte
    luck_boost = get_luck_probability_boost(parent.luck)

    # Generar múltiples candidatos (más luck = más candidatos)
    num_candidates = 1 + int(luck_boost * 4)  # 1-3 candidatos

    candidates = []

    for _ in range(num_candidates):
        offspring = parent.copy()

        # Mutación estándar
        for i in range(problem.nvars):
            if random.random() < mutation_rate:
                lower, upper = problem.types[i]
                range_size = upper - lower

                # Mutación moderada
                max_change = range_size * 0.15
                delta = random.gauss(0, max_change / 3)
                new_value = offspring.variables[i] + delta

                offspring.variables[i] = max(lower, min(upper, new_value))

        offspring.evaluated = False
        candidates.append(offspring)

    # Evaluar todos y retornar el mejor
    for candidate in candidates:
        problem.evaluate(candidate)

    # Elegir mejor según primer objetivo (minimización)
    best = min(candidates, key=lambda s: s.objectives[0] if s.objectives else float('inf'))

    return best


# =============================================================================
# MUTACIÓN GUIADA POR WISDOM
# =============================================================================

def wisdom_guided_mutation(
    parent: RPGSolution,
    problem: Any,
    pareto_front: Optional[List[RPGSolution]] = None,
    mutation_rate: float = 0.3
) -> RPGSolution:
    """
    Mutación guiada por información del frente de Pareto (Wisdom).

    Parameters
    ----------
    parent : RPGSolution
        Solución padre
    problem : object
        Problema de optimización
    pareto_front : List[RPGSolution], optional
        Frente de Pareto actual (para aprendizaje)
    mutation_rate : float, optional
        Probabilidad de mutación (default: 0.3)

    Returns
    -------
    RPGSolution
        Offspring guiado por conocimiento previo

    Notes
    -----
    - Alta Wisdom -> aprende de soluciones exitosas en frente de Pareto
    - Dirige mutaciones hacia regiones prometedoras
    - Si no hay frente, usa mutación adaptativa estándar

    Examples
    --------
    >>> offspring = wisdom_guided_mutation(parent, problem, pareto_front)
    >>> # Offspring se mueve hacia región de soluciones Pareto-óptimas
    """
    offspring = parent.copy()

    if pareto_front and len(pareto_front) > 0 and parent.wisdom > 50:
        # Aprender del frente de Pareto
        # Elegir una solución del frente como referencia
        reference = random.choice(pareto_front)

        # Factor de aprendizaje basado en wisdom
        wisdom_factor = (parent.wisdom - 20) / 80  # [0, 1]

        for i in range(problem.nvars):
            if random.random() < mutation_rate:
                lower, upper = problem.types[i]

                # Mover hacia la referencia, modulado por wisdom
                direction = reference.variables[i] - offspring.variables[i]
                step = direction * wisdom_factor * random.uniform(0.1, 0.5)

                new_value = offspring.variables[i] + step

                # Respetar límites
                offspring.variables[i] = max(lower, min(upper, new_value))

    else:
        # Sin frente o baja wisdom: mutación estándar
        return adaptive_mutation(parent, problem, mutation_rate)

    offspring.evaluated = False
    return offspring


# =============================================================================
# ESTABILIDAD POR ENDURANCE (formalismo, modo "variation")
# =============================================================================

# Amplificación por defecto del paso efectivo para END baja a presión máxima.
DEFAULT_ENDURANCE_AMPLIFICATION = 2.0


def endurance_damping_factor(
    endurance: float,
    pressure: float,
    amplification: float = DEFAULT_ENDURANCE_AMPLIFICATION
) -> float:
    """
    Factor de escala del paso efectivo (sigma) por estabilidad de Endurance.

    Parameters
    ----------
    endurance : float
        Valor del atributo endurance (20-100)
    pressure : float
        Presión de selección normalizada en [0, 1]. Proxy documentado:
        generaciones de estancamiento (sin mejora) normalizadas por el
        algoritmo llamante.
    amplification : float, optional
        Amplificación máxima a presión 1.0 y estabilidad 0 (default: 2.0)

    Returns
    -------
    float
        Factor multiplicativo >= 1 aplicado al sigma de la mutación

    Notes
    -----
    Mecanismo D1->B (formalismo): la selección es fitness-pura y END actúa
    dentro de la VARIACIÓN como estabilidad conductual.

    sigma_efectivo = sigma * (1 + pressure * (1 - estabilidad) * amplificacion)
    con estabilidad = endurance_normalizada * 0.8 (ver
    core.rpg_attributes.get_endurance_stability).

    - pressure = 0 -> factor 1.0 para cualquier END (sin amplificación).
    - END alta bajo presión -> el individuo conserva sus pasos compuestos.
    - END baja bajo presión -> pasos amplificados/erráticos (más exploración).

    Examples
    --------
    >>> endurance_damping_factor(50, pressure=0.0)
    1.0
    >>> endurance_damping_factor(20, pressure=1.0)  # estabilidad 0.0
    3.0
    >>> endurance_damping_factor(100, pressure=1.0)  # estabilidad 0.8
    1.4
    """
    stability = get_endurance_stability(endurance)
    return 1.0 + pressure * (1.0 - stability) * amplification


def endurance_stability_mutation(
    parent: RPGSolution,
    problem: Any,
    pressure: float = 0.0,
    mutation_rate: float = 0.3,
    amplification: float = DEFAULT_ENDURANCE_AMPLIFICATION
) -> RPGSolution:
    """
    Mutación de estabilidad: pasos compuestos amortiguados por Endurance.

    Es la rama explícita para individuos END-dominantes en el modo
    "variation" (formalismo): sustituye al fallback silencioso por mutación
    adaptativa del modo legacy "selection".

    Parameters
    ----------
    parent : RPGSolution
        Solución padre
    problem : object
        Problema con atributos nvars y types (límites)
    pressure : float, optional
        Presión de selección normalizada en [0, 1] (default: 0.0)
    mutation_rate : float, optional
        Probabilidad de mutar cada variable (default: 0.3)
    amplification : float, optional
        Amplificación máxima del paso para END baja (default: 2.0)

    Returns
    -------
    RPGSolution
        Offspring mutado

    Notes
    -----
    Usa la magnitud de paso de la mutación adaptativa (basada en Strength)
    escalada por el factor de amortiguación de Endurance:

    - END alta bajo presión alta -> conserva el paso compuesto (sigma
      estable, refinamiento local).
    - END baja bajo presión alta -> sigma amplificado, pasos erráticos que
      incrementan la exploración.

    Examples
    --------
    >>> offspring = endurance_stability_mutation(parent, problem, pressure=0.5)
    """
    offspring = parent.copy()

    # Magnitud base (misma fórmula que la mutación adaptativa)
    strength_mod = get_mutation_strength_modifier(parent.strength)

    # Amortiguación conductual por Endurance
    damping = endurance_damping_factor(parent.endurance, pressure,
                                       amplification)

    for i in range(problem.nvars):
        if random.random() < mutation_rate:
            lower, upper = problem.types[i]
            range_size = upper - lower

            max_change = range_size * (0.05 + strength_mod * 0.25) * damping

            delta = random.gauss(0, max_change / 3)
            new_value = offspring.variables[i] + delta

            # Respetar límites
            offspring.variables[i] = max(lower, min(upper, new_value))

    offspring.evaluated = False
    return offspring


# =============================================================================
# OPERADOR COMPUESTO
# =============================================================================

def rpg_mutate(
    parent: RPGSolution,
    problem: Any,
    pareto_front: Optional[List[RPGSolution]] = None,
    give_xp: bool = False,
    pressure: float = 0.0,
    endurance_mode: str = 'variation'
) -> RPGSolution:
    """
    Operador de mutación compuesto que elige según perfil RPG.

    Parameters
    ----------
    parent : RPGSolution
        Solución padre
    problem : object
        Problema de optimización
    pareto_front : List[RPGSolution], optional
        Frente de Pareto para wisdom-guided mutation
    give_xp : bool, optional
        Si otorgar XP al padre tras mutación exitosa (default: False)
    pressure : float, optional
        Presión de selección normalizada en [0, 1]: proxy de estancamiento
        (generaciones sin mejora) pasado por el algoritmo (default: 0.0).
        Solo se usa en el modo "variation".
    endurance_mode : str, optional
        "variation" (default, formalismo de tesis): la selección es
        fitness-pura y END actúa dentro de la variación como estabilidad
        conductual; la rama END-dominante usa la mutación de estabilidad
        amortiguada por presión. "selection" (legacy pre-formalismo):
        preserva el comportamiento enviado, con el fallback silencioso a
        mutación adaptativa para END-dominantes.

    Returns
    -------
    RPGSolution
        Offspring mutado usando operador apropiado

    Notes
    -----
    Selecciona operador según atributo dominante:
    - Strength dominante -> adaptive_mutation
    - Dexterity dominante -> fine_tune_mutation
    - Wisdom dominante -> wisdom_guided_mutation
    - Luck dominante -> luck_based_mutation
    - Endurance dominante -> endurance_stability_mutation ("variation")
                            o adaptive_mutation ("selection", legacy)
    - Balanceado -> elige aleatoriamente

    Raises
    ------
    ValueError
        Si endurance_mode no es "variation" ni "selection"

    Examples
    --------
    >>> offspring = rpg_mutate(parent, problem)
    >>> # Operador elegido según atributos de parent
    """
    if endurance_mode not in ('variation', 'selection'):
        raise ValueError(
            f"endurance_mode debe ser 'variation' o 'selection', "
            f"no {endurance_mode!r}"
        )

    dominant = parent.get_dominant_attribute()

    # Seleccionar operador según atributo dominante
    if dominant == 'strength':
        offspring = adaptive_mutation(parent, problem)
    elif dominant == 'dexterity':
        offspring = fine_tune_mutation(parent, problem)
    elif dominant == 'wisdom':
        offspring = wisdom_guided_mutation(parent, problem, pareto_front)
    elif dominant == 'luck':
        offspring = luck_based_mutation(parent, problem)
    elif dominant == 'endurance':
        if endurance_mode == 'variation':
            # Formalismo: estabilidad conductual amortiguada por presión
            offspring = endurance_stability_mutation(parent, problem,
                                                     pressure=pressure)
        else:
            # Legacy "selection": fallback silencioso a adaptativa (sin END)
            offspring = adaptive_mutation(parent, problem)
    else:
        # Por defecto
        offspring = adaptive_mutation(parent, problem)

    return offspring


# =============================================================================
# MUTACIÓN POLIMÓRFICA (múltiples estrategias)
# =============================================================================

def polymorphic_mutation(
    parent: RPGSolution,
    problem: Any,
    pareto_front: Optional[List[RPGSolution]] = None
) -> RPGSolution:
    """
    Mutación polimórfica que combina múltiples estrategias.

    Parameters
    ----------
    parent : RPGSolution
        Solución padre
    problem : object
        Problema de optimización
    pareto_front : List[RPGSolution], optional
        Frente de Pareto actual

    Returns
    -------
    RPGSolution
        Offspring con mutación híbrida

    Notes
    -----
    Aplica secuencialmente:
    1. Mutación adaptativa (Strength)
    2. Ajuste fino (Dexterity)
    3. Guiado por Wisdom (si hay frente)

    Útil para soluciones de alto nivel que pueden beneficiarse
    de múltiples estrategias simultáneas.

    Examples
    --------
    >>> offspring = polymorphic_mutation(parent, problem, pareto_front)
    >>> # Combina exploración, refinamiento y aprendizaje
    """
    # Paso 1: Mutación adaptativa moderada
    offspring = adaptive_mutation(parent, problem, mutation_rate=0.2)

    # Paso 2: Ajuste fino
    offspring = fine_tune_mutation(offspring, problem, mutation_rate=0.3)

    # Paso 3: Guiado por wisdom si disponible
    if pareto_front and len(pareto_front) > 0 and parent.wisdom > 60:
        offspring = wisdom_guided_mutation(offspring, problem, pareto_front, mutation_rate=0.2)

    return offspring
