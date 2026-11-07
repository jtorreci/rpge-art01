"""
Operadores de cruce RPG adaptativos.

Los operadores de cruce combinan soluciones parentales usando atributos RPG
para guiar la herencia genética de forma inteligente.
"""
import random
import copy
from typing import Dict, List, Any, Optional


# =============================================================================
# HERENCIA DE ATRIBUTOS
# =============================================================================

def inherit_attributes(
    parent1_attrs: Dict[str, float],
    parent2_attrs: Dict[str, float],
    inheritance_bias: float = 0.5
) -> Dict[str, float]:
    """
    Heredar atributos RPG de dos padres.

    Parameters
    ----------
    parent1_attrs : Dict[str, float]
        Atributos del primer padre
    parent2_attrs : Dict[str, float]
        Atributos del segundo padre
    inheritance_bias : float, optional
        Sesgo hacia parent1 (0.5 = balanceado)

    Returns
    -------
    Dict[str, float]
        Atributos del offspring

    Notes
    -----
    Mezcla atributos usando interpolación con variación aleatoria.
    Cada atributo tiene una probabilidad de heredarse más de un padre.
    """
    from core.rpg_attributes import clamp_attribute

    offspring_attrs = {}

    for attr_name in parent1_attrs.keys():
        val1 = parent1_attrs[attr_name]
        val2 = parent2_attrs[attr_name]

        # Interpolación con pequeña variación
        alpha = inheritance_bias + random.uniform(-0.2, 0.2)
        alpha = max(0.0, min(1.0, alpha))

        # Mezclar
        inherited = alpha * val1 + (1 - alpha) * val2

        # Pequeña mutación (±5%)
        mutation = random.uniform(-5, 5)
        inherited += mutation

        # Clamp
        offspring_attrs[attr_name] = clamp_attribute(inherited)

    return offspring_attrs


# =============================================================================
# OPERADORES DE CRUCE ESPECIALIZADOS
# =============================================================================

def wisdom_crossover(parent1, parent2, problem) -> Any:
    """
    Cruce guiado por Wisdom - aprende del mejor padre.

    Parameters
    ----------
    parent1 : RPGSolution
        Primer padre
    parent2 : RPGSolution
        Segundo padre
    problem : Problem
        Problema de optimización

    Returns
    -------
    RPGSolution
        Offspring que hereda más del mejor padre

    Notes
    -----
    Alta wisdom identifica al mejor padre y hereda principalmente de él.
    El padre con mejor fitness contribuye más genes.
    """
    from core.rpg_solution import RPGSolution

    # Identificar mejor padre (menor costo = mejor)
    if not parent1.objectives or not parent2.objectives:
        # Si no hay evaluación, usar balanceado
        return balanced_crossover(parent1, parent2, problem)

    cost1 = parent1.objectives[0]
    cost2 = parent2.objectives[0]

    better_parent = parent1 if cost1 < cost2 else parent2
    worse_parent = parent2 if cost1 < cost2 else parent1

    # Wisdom promedio determina qué tanto aprender del mejor
    avg_wisdom = (parent1.wisdom + parent2.wisdom) / 2
    learning_bias = 0.5 + (avg_wisdom / 100) * 0.3  # 0.5 to 0.8

    # Crear offspring
    offspring = RPGSolution(problem)

    # Heredar variables con sesgo hacia el mejor
    offspring.variables = []
    for i in range(len(better_parent.variables)):
        if random.random() < learning_bias:
            # Del mejor padre
            value = better_parent.variables[i]
        else:
            # Del peor padre
            value = worse_parent.variables[i]

        # Pequeña variación
        bounds = problem.types[i]
        noise = random.uniform(-0.05, 0.05) * (bounds[1] - bounds[0])
        value = max(bounds[0], min(bounds[1], value + noise))

        offspring.variables.append(value)

    # Heredar atributos RPG
    bias = learning_bias
    offspring_attrs = inherit_attributes(
        better_parent.get_attributes(),
        worse_parent.get_attributes(),
        inheritance_bias=bias
    )

    offspring.strength = offspring_attrs['strength']
    offspring.wisdom = offspring_attrs['wisdom']
    offspring.endurance = offspring_attrs['endurance']
    offspring.dexterity = offspring_attrs['dexterity']
    offspring.luck = offspring_attrs['luck']

    # Nivel inicial
    offspring.level = 1
    offspring.xp = 0

    return offspring


def balanced_crossover(parent1, parent2, problem) -> Any:
    """
    Cruce balanceado - toma equitativamente de ambos padres.

    Parameters
    ----------
    parent1 : RPGSolution
        Primer padre
    parent2 : RPGSolution
        Segundo padre
    problem : Problem
        Problema de optimización

    Returns
    -------
    RPGSolution
        Offspring con mezcla balanceada

    Notes
    -----
    Cruce clásico de un punto con herencia 50/50 de atributos.
    """
    from core.rpg_solution import RPGSolution

    offspring = RPGSolution(problem)

    # Cruce de un punto
    crossover_point = random.randint(1, len(parent1.variables) - 1)

    offspring.variables = []
    for i in range(len(parent1.variables)):
        if i < crossover_point:
            value = parent1.variables[i]
        else:
            value = parent2.variables[i]

        offspring.variables.append(value)

    # Heredar atributos balanceados
    offspring_attrs = inherit_attributes(
        parent1.get_attributes(),
        parent2.get_attributes(),
        inheritance_bias=0.5  # Perfectamente balanceado
    )

    offspring.strength = offspring_attrs['strength']
    offspring.wisdom = offspring_attrs['wisdom']
    offspring.endurance = offspring_attrs['endurance']
    offspring.dexterity = offspring_attrs['dexterity']
    offspring.luck = offspring_attrs['luck']

    # Nivel inicial
    offspring.level = 1
    offspring.xp = 0

    return offspring


def dominant_crossover(parent1, parent2, problem) -> Any:
    """
    Cruce con herencia dominante - favorece al más fuerte.

    Parameters
    ----------
    parent1 : RPGSolution
        Primer padre
    parent2 : RPGSolution
        Segundo padre
    problem : Problem
        Problema de optimización

    Returns
    -------
    RPGSolution
        Offspring que hereda del padre dominante

    Notes
    -----
    El padre con mayor nivel y strength es considerado dominante.
    Offspring hereda principalmente atributos del dominante.
    """
    from core.rpg_solution import RPGSolution

    # Calcular poder de combate (level + strength)
    power1 = parent1.level + parent1.strength / 100
    power2 = parent2.level + parent2.strength / 100

    dominant = parent1 if power1 > power2 else parent2
    recessive = parent2 if power1 > power2 else parent1

    # Sesgo hacia dominante (70% dominante, 30% recesivo)
    dominance_bias = 0.7

    # Crear offspring
    offspring = RPGSolution(problem)

    # Heredar variables
    offspring.variables = []
    for i in range(len(dominant.variables)):
        if random.random() < dominance_bias:
            value = dominant.variables[i]
        else:
            value = recessive.variables[i]

        offspring.variables.append(value)

    # Heredar atributos con sesgo
    offspring_attrs = inherit_attributes(
        dominant.get_attributes(),
        recessive.get_attributes(),
        inheritance_bias=dominance_bias
    )

    offspring.strength = offspring_attrs['strength']
    offspring.wisdom = offspring_attrs['wisdom']
    offspring.endurance = offspring_attrs['endurance']
    offspring.dexterity = offspring_attrs['dexterity']
    offspring.luck = offspring_attrs['luck']

    # Nivel inicial (puede heredar algo del dominante)
    offspring.level = 1
    offspring.xp = 0

    return offspring


def lucky_crossover(parent1, parent2, problem) -> Any:
    """
    Cruce afortunado - alta luck encuentra buenas combinaciones.

    Parameters
    ----------
    parent1 : RPGSolution
        Primer padre
    parent2 : RPGSolution
        Segundo padre
    problem : Problem
        Problema de optimización

    Returns
    -------
    RPGSolution
        Mejor offspring de múltiples intentos

    Notes
    -----
    Alta luck genera múltiples candidatos y selecciona el mejor.
    Número de intentos: 1 + round(avg_luck / 40).
    """
    from core.rpg_solution import RPGSolution

    # Luck promedio determina cuántos intentos
    avg_luck = (parent1.luck + parent2.luck) / 2
    n_attempts = 1 + round(avg_luck / 40)  # 1-3 intentos
    n_attempts = min(3, max(1, n_attempts))

    candidates = []

    for _ in range(n_attempts):
        # Generar candidato con cruce aleatorio
        offspring = RPGSolution(problem)

        offspring.variables = []
        for i in range(len(parent1.variables)):
            # 50/50 de cada padre
            value = random.choice([parent1.variables[i], parent2.variables[i]])

            # Pequeña variación afortunada
            bounds = problem.types[i]
            luck_factor = avg_luck / 100
            noise = random.uniform(-0.03, 0.03) * luck_factor * (bounds[1] - bounds[0])
            value = max(bounds[0], min(bounds[1], value + noise))

            offspring.variables.append(value)

        # Heredar atributos
        offspring_attrs = inherit_attributes(
            parent1.get_attributes(),
            parent2.get_attributes(),
            inheritance_bias=random.uniform(0.3, 0.7)
        )

        offspring.strength = offspring_attrs['strength']
        offspring.wisdom = offspring_attrs['wisdom']
        offspring.endurance = offspring_attrs['endurance']
        offspring.dexterity = offspring_attrs['dexterity']
        offspring.luck = offspring_attrs['luck']

        offspring.level = 1
        offspring.xp = 0

        # Evaluar candidato
        problem.evaluate(offspring)
        candidates.append(offspring)

    # Retornar el mejor candidato (menor costo)
    best = min(candidates, key=lambda s: s.objectives[0] if s.objectives else float('inf'))
    return best


# =============================================================================
# OPERADOR COMPUESTO
# =============================================================================

def rpg_crossover(
    parent1,
    parent2,
    problem,
    give_xp: bool = False
) -> Any:
    """
    Operador de cruce compuesto que elige según atributos dominantes.

    Parameters
    ----------
    parent1 : RPGSolution
        Primer padre
    parent2 : RPGSolution
        Segundo padre
    problem : Problem
        Problema de optimización
    give_xp : bool, optional
        Si otorgar XP a los padres (default: False)

    Returns
    -------
    RPGSolution
        Offspring creado

    Notes
    -----
    Selecciona operador según atributo dominante:
    - Wisdom > 70: wisdom_crossover
    - Luck > 70: lucky_crossover
    - Strength > 70: dominant_crossover
    - Else: balanced_crossover
    """
    # Promediar atributos de ambos padres
    avg_wisdom = (parent1.wisdom + parent2.wisdom) / 2
    avg_luck = (parent1.luck + parent2.luck) / 2
    avg_strength = (parent1.strength + parent2.strength) / 2

    # Seleccionar operador
    if avg_wisdom > 70:
        offspring = wisdom_crossover(parent1, parent2, problem)
    elif avg_luck > 70:
        offspring = lucky_crossover(parent1, parent2, problem)
    elif avg_strength > 70:
        offspring = dominant_crossover(parent1, parent2, problem)
    else:
        offspring = balanced_crossover(parent1, parent2, problem)

    # Otorgar XP si se solicita
    if give_xp:
        parent1.gain_xp(25)  # XP por reproducción
        parent2.gain_xp(25)

    return offspring
