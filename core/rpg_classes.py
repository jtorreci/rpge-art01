"""
Sistema de clases RPG para soluciones.

Define arquetipos de soluciones según sus perfiles de atributos: cinco
clases, una por sector del glifo de perfil del artículo (formalismo art01,
S3.7). Las clases son una lectura del vector de atributos y no llevan
multiplicadores de comportamiento: no tienen poder causal.
"""
from enum import Enum
from typing import Dict, List, Tuple
from collections import Counter


# =============================================================================
# DEFINICIONES DE CLASES
# =============================================================================

class RPGClassType(Enum):
    """Tipos de clases RPG disponibles, en orden canónico de los sectores."""
    WARRIOR = 'warrior'
    MONK = 'monk'
    ROGUE = 'rogue'
    SCOUT = 'scout'
    PALADIN = 'paladin'


# Descripciones de cada clase
CLASS_DESCRIPTIONS = {
    'warrior': (
        'Guerrero ofensivo especializado en exploración agresiva. '
        'Alta Strength y Endurance permiten cambios grandes y resistencia a eliminación. '
        'Ideal para búsqueda global en fases iniciales.'
    ),
    'monk': (
        'Refinador persistente que no pierde la disciplina bajo presión. '
        'Alta Endurance y Dexterity combinan estabilidad con ajustes cada vez más finos. '
        'Ideal para convergencia sostenida en valles estrechos.'
    ),
    'rogue': (
        'Especialista en movimientos precisos y oportunistas. '
        'Alta Dexterity y Luck logran ajustes perfectos en momentos clave. '
        'Encuentra soluciones inesperadas.'
    ),
    'scout': (
        'Explorador inteligente con intuición afortunada. '
        'Alta Luck y Wisdom descubren regiones prometedoras. '
        'Balance entre aprendizaje y serendipia.'
    ),
    'paladin': (
        'Explorador guiado por el conocimiento acumulado. '
        'Alta Wisdom y Strength combinan aprendizaje del frente con pasos amplios. '
        'Ideal para abrir regiones nuevas con dirección.'
    )
}


# Atributos primarios de cada clase (los 2 más importantes). El orden de las
# claves es el canónico: los cinco pares son las aristas del ciclo de canales
# STR-END-DEX-LCK-WIS, es decir los cinco sectores del glifo (art01, S3.7).
CLASS_PRIMARY_ATTRIBUTES = {
    'warrior': ['strength', 'endurance'],
    'monk': ['endurance', 'dexterity'],
    'rogue': ['dexterity', 'luck'],
    'scout': ['luck', 'wisdom'],
    'paladin': ['wisdom', 'strength'],
}


# =============================================================================
# ASIGNACIÓN DE CLASE
# =============================================================================

def assign_rpg_class(attributes: Dict[str, float]) -> str:
    """
    Asignar clase RPG según perfil de atributos.

    Parameters
    ----------
    attributes : Dict[str, float]
        Diccionario con atributos RPG

    Returns
    -------
    str
        Nombre de la clase asignada

    Notes
    -----
    La asignación se basa en la suma de los dos atributos primarios de cada
    clase. Se elige la clase con mayor suma; los empates se resuelven por el
    orden canónico de ``CLASS_PRIMARY_ATTRIBUTES`` (warrior, monk, rogue,
    scout, paladin), que es el orden de los sectores del glifo de perfil
    (formalismo art01, S3.7).

    Examples
    --------
    >>> attrs = {'strength': 90, 'wisdom': 40, 'endurance': 85,
    ...          'dexterity': 45, 'luck': 35}
    >>> assign_rpg_class(attrs)
    'warrior'  # strength (90) + endurance (85) = 175
    >>> assign_rpg_class({name: 50 for name in attrs})
    'warrior'  # empate a 100: gana el primero en orden canónico
    """
    class_scores = {
        class_name: sum(attributes.get(attr, 0) for attr in primary_attrs)
        for class_name, primary_attrs in CLASS_PRIMARY_ATTRIBUTES.items()
    }

    # max() devuelve la primera clave con el valor máximo en el orden de
    # inserción del diccionario, que es el orden canónico declarado arriba.
    return max(class_scores, key=class_scores.get)


def get_class_score(attributes: Dict[str, float], class_name: str) -> float:
    """
    Calcular qué tan bien encaja un perfil en una clase.

    Parameters
    ----------
    attributes : Dict[str, float]
        Atributos RPG
    class_name : str
        Nombre de la clase

    Returns
    -------
    float
        Score de ajuste (0-200, suma de atributos primarios)

    Examples
    --------
    >>> attrs = {'strength': 90, 'endurance': 85, ...}
    >>> get_class_score(attrs, 'warrior')
    175.0
    """
    primary_attrs = CLASS_PRIMARY_ATTRIBUTES.get(class_name, [])
    return sum(attributes.get(attr, 0) for attr in primary_attrs)


# =============================================================================
# BONIFICACIONES POR CLASE
# =============================================================================

def get_class_bonus(class_name: str) -> Dict[str, str]:
    """
    Obtener los rasgos de una clase.

    Parameters
    ----------
    class_name : str
        Nombre de la clase

    Returns
    -------
    Dict[str, str]
        Diccionario con la descripción de la clase; sin valores numéricos

    Notes
    -----
    Las clases no tienen poder causal (formalismo art01, S3.7): son una
    lectura del vector de atributos y no llevan multiplicadores de
    comportamiento. Todo efecto conductual fluye por los modificadores de
    ``core.rpg_attributes``. La función se conserva con la misma firma por
    compatibilidad, pero no devuelve ningún multiplicador.

    Examples
    --------
    >>> get_class_bonus('warrior')['description']
    'Exploración agresiva'
    >>> get_class_bonus('paladin')['description']
    'Exploración guiada'
    """
    descriptions = {
        'warrior': 'Exploración agresiva',
        'monk': 'Refinamiento persistente',
        'rogue': 'Movimientos perfectos',
        'scout': 'Descubrimiento guiado',
        'paladin': 'Exploración guiada',
    }

    return {'description': descriptions.get(class_name, '')}


# =============================================================================
# ESTADÍSTICAS DE CLASES
# =============================================================================

def count_classes_in_population(population: List) -> Dict[str, int]:
    """
    Contar distribución de clases en una población.

    Parameters
    ----------
    population : List[RPGSolution]
        Población de soluciones

    Returns
    -------
    Dict[str, int]
        Contador de cada clase

    Examples
    --------
    >>> count_classes_in_population(population)
    {'warrior': 25, 'scout': 18, 'rogue': 15, 'monk': 22, 'paladin': 20}
    """
    classes = [sol.get_rpg_class() for sol in population]
    return dict(Counter(classes))


def get_dominant_class(population: List) -> str:
    """
    Identificar la clase más común en la población.

    Parameters
    ----------
    population : List[RPGSolution]
        Población de soluciones

    Returns
    -------
    str
        Clase dominante

    Examples
    --------
    >>> get_dominant_class(population)
    'warrior'
    """
    class_counts = count_classes_in_population(population)

    if not class_counts:
        return 'warrior'  # Default

    return max(class_counts, key=class_counts.get)


def get_class_distribution_stats(population: List) -> Dict:
    """
    Obtener estadísticas detalladas de distribución de clases.

    Parameters
    ----------
    population : List[RPGSolution]
        Población de soluciones

    Returns
    -------
    Dict
        Estadísticas con conteos, porcentajes y clase dominante

    Examples
    --------
    >>> stats = get_class_distribution_stats(population)
    >>> print(stats['percentages']['warrior'])
    25.0  # 25% de la población
    """
    class_counts = count_classes_in_population(population)
    total = len(population)

    percentages = {
        class_name: (count / total * 100) if total > 0 else 0
        for class_name, count in class_counts.items()
    }

    return {
        'counts': class_counts,
        'percentages': percentages,
        'total': total,
        'dominant_class': get_dominant_class(population),
        'diversity': len(class_counts)  # Número de clases presentes
    }


# =============================================================================
# ANÁLISIS DE CLASES
# =============================================================================

def analyze_class_performance(
    population: List,
    metric: str = 'cost'
) -> Dict[str, Dict]:
    """
    Analizar rendimiento por clase.

    Parameters
    ----------
    population : List[RPGSolution]
        Población de soluciones evaluadas
    metric : str, optional
        Métrica a analizar: 'cost', 'safety', 'level' (default: 'cost')

    Returns
    -------
    Dict[str, Dict]
        Estadísticas por clase (promedio, mejor, peor)

    Examples
    --------
    >>> stats = analyze_class_performance(population, metric='cost')
    >>> print(stats['warrior']['average'])
    285.5
    """
    # Agrupar por clase
    classes_data = {}

    for sol in population:
        if not sol.objectives:
            continue

        class_name = sol.get_rpg_class()

        if class_name not in classes_data:
            classes_data[class_name] = []

        # Extraer métrica
        if metric == 'cost':
            value = sol.objectives[0]
        elif metric == 'safety':
            value = -sol.objectives[1]  # Cv (negativo en objetivos)
        elif metric == 'level':
            value = sol.level
        else:
            value = sol.objectives[0]

        classes_data[class_name].append(value)

    # Calcular estadísticas
    stats = {}

    for class_name, values in classes_data.items():
        if not values:
            continue

        stats[class_name] = {
            'average': sum(values) / len(values),
            'best': min(values) if metric == 'cost' else max(values),
            'worst': max(values) if metric == 'cost' else min(values),
            'count': len(values)
        }

    return stats


def get_class_leaderboard(
    population: List,
    metric: str = 'cost',
    ascending: bool = True
) -> List[Tuple[str, float]]:
    """
    Obtener ranking de clases por rendimiento.

    Parameters
    ----------
    population : List[RPGSolution]
        Población evaluada
    metric : str, optional
        Métrica de ranking (default: 'cost')
    ascending : bool, optional
        Si ordenar ascendente (mejor = menor) (default: True)

    Returns
    -------
    List[Tuple[str, float]]
        Lista ordenada de (clase, promedio)

    Examples
    --------
    >>> leaderboard = get_class_leaderboard(population, 'cost')
    >>> print(leaderboard)
    [('paladin', 265.3), ('rogue', 270.1), ('warrior', 275.8), ...]
    """
    stats = analyze_class_performance(population, metric)

    leaderboard = [
        (class_name, data['average'])
        for class_name, data in stats.items()
    ]

    # Ordenar
    leaderboard.sort(key=lambda x: x[1], reverse=not ascending)

    return leaderboard


# =============================================================================
# INFORMACIÓN Y UTILIDADES
# =============================================================================

def get_class_info(class_name: str) -> Dict:
    """
    Obtener información completa de una clase.

    Parameters
    ----------
    class_name : str
        Nombre de la clase

    Returns
    -------
    Dict
        Información completa (descripción, atributos, bonificaciones)

    Examples
    --------
    >>> info = get_class_info('warrior')
    >>> print(info['description'])
    'Guerrero ofensivo especializado en exploración agresiva...'
    """
    return {
        'name': class_name,
        'description': CLASS_DESCRIPTIONS.get(class_name, ''),
        'primary_attributes': CLASS_PRIMARY_ATTRIBUTES.get(class_name, []),
        'bonuses': get_class_bonus(class_name)
    }


def get_all_classes_info() -> Dict[str, Dict]:
    """
    Obtener información de todas las clases.

    Returns
    -------
    Dict[str, Dict]
        Diccionario con info de cada clase

    Examples
    --------
    >>> all_info = get_all_classes_info()
    >>> for class_name, info in all_info.items():
    ...     print(f"{class_name}: {info['description'][:50]}...")
    """
    return {
        class_name: get_class_info(class_name)
        for class_name in CLASS_PRIMARY_ATTRIBUTES.keys()
    }
