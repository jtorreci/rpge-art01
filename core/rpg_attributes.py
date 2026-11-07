"""
Sistema de atributos RPG.

Define constantes, funciones de modificadores, validación y utilidades
para el sistema de atributos tipo RPG (Strength, Wisdom, Endurance, Dexterity, Luck).
"""
import random
from typing import Dict


# =============================================================================
# CONSTANTES
# =============================================================================

ATTRIBUTE_NAMES = ['strength', 'wisdom', 'endurance', 'dexterity', 'luck']

ATTRIBUTE_MIN = 20
ATTRIBUTE_MAX = 100

POINTS_PER_LEVEL = 5


# =============================================================================
# DESCRIPCIONES DE ATRIBUTOS
# =============================================================================

ATTRIBUTE_DESCRIPTIONS = {
    'strength': (
        'Capacidad de realizar cambios grandes y agresivos en las soluciones. '
        'Afecta la magnitud de las mutaciones y la exploración del espacio de búsqueda.'
    ),
    'wisdom': (
        'Habilidad para aprender de la experiencia y usar información del frente de Pareto. '
        'Influye en la tasa de aprendizaje y en la explotación de conocimiento previo.'
    ),
    'endurance': (
        'Resistencia a ser eliminada de la población. '
        'Aumenta la probabilidad de supervivencia en selección y evita reemplazos prematuros.'
    ),
    'dexterity': (
        'Precisión en ajustes finos y mutaciones sutiles. '
        'Controla la granularidad de los cambios y la convergencia refinada.'
    ),
    'luck': (
        'Sesgo favorable en eventos aleatorios. '
        'Proporciona bonificaciones en selección, mutación y operadores estocásticos.'
    )
}


# =============================================================================
# MODIFICADORES DE ATRIBUTOS
# =============================================================================

def get_mutation_strength_modifier(strength: float) -> float:
    """
    Calcular modificador de fuerza de mutación.

    Parameters
    ----------
    strength : float
        Valor del atributo strength (20-100)

    Returns
    -------
    float
        Modificador en rango [0, 1], donde mayor strength = mayor modificador

    Notes
    -----
    Normaliza el atributo strength al rango [0, 1] para usar como
    factor multiplicativo en operadores de mutación.

    Examples
    --------
    >>> get_mutation_strength_modifier(20)
    0.0
    >>> get_mutation_strength_modifier(100)
    1.0
    >>> get_mutation_strength_modifier(60)
    0.5
    """
    return (strength - ATTRIBUTE_MIN) / (ATTRIBUTE_MAX - ATTRIBUTE_MIN)


def get_wisdom_learning_rate(wisdom: float) -> float:
    """
    Calcular tasa de aprendizaje basada en sabiduría.

    Parameters
    ----------
    wisdom : float
        Valor del atributo wisdom (20-100)

    Returns
    -------
    float
        Tasa de aprendizaje en rango [0, 1]

    Notes
    -----
    Mayor wisdom aumenta la capacidad de aprender del frente de Pareto
    y de soluciones exitosas previas.

    Examples
    --------
    >>> get_wisdom_learning_rate(20)
    0.0
    >>> get_wisdom_learning_rate(100)
    1.0
    """
    return (wisdom - ATTRIBUTE_MIN) / (ATTRIBUTE_MAX - ATTRIBUTE_MIN)


def get_endurance_survival_bonus(endurance: float) -> float:
    """
    Calcular bonus de supervivencia por resistencia.

    Parameters
    ----------
    endurance : float
        Valor del atributo endurance (20-100)

    Returns
    -------
    float
        Bonus de supervivencia (>=0), mayor endurance = mayor bonus

    Notes
    -----
    Este bonus se suma a la probabilidad de supervivencia en selección.
    Rango: [0, 0.8] para evitar que soluciones de baja calidad sobrevivan
    solo por alta endurance.

    Examples
    --------
    >>> get_endurance_survival_bonus(20)
    0.0
    >>> get_endurance_survival_bonus(100)
    0.8
    """
    normalized = (endurance - ATTRIBUTE_MIN) / (ATTRIBUTE_MAX - ATTRIBUTE_MIN)
    return normalized * 0.8


def get_endurance_stability(endurance: float) -> float:
    """
    Calcular estabilidad conductual por resistencia (formalismo, modo "variation").

    Parameters
    ----------
    endurance : float
        Valor del atributo endurance (20-100)

    Returns
    -------
    float
        Estabilidad en rango [0, 0.8], mayor endurance = mayor estabilidad

    Notes
    -----
    En el modo "variation" la selección es fitness-pura y END actúa dentro
    de la VARIACIÓN como estabilidad conductual: a presión de selección alta,
    los individuos con END alta conservan sus pasos compuestos de mutación,
    mientras que los individuos con END baja reciben pasos amplificados.

    Reutiliza el patrón de normalización lineal existente:
    estabilidad = endurance_normalizada * 0.8, con
    endurance_normalizada = (endurance - 20) / (100 - 20).

    Examples
    --------
    >>> get_endurance_stability(20)
    0.0
    >>> get_endurance_stability(100)
    0.8
    >>> get_endurance_stability(60)
    0.4
    """
    normalized = (endurance - ATTRIBUTE_MIN) / (ATTRIBUTE_MAX - ATTRIBUTE_MIN)
    return normalized * 0.8


def get_dexterity_precision(dexterity: float) -> float:
    """
    Calcular precisión basada en destreza.

    Parameters
    ----------
    dexterity : float
        Valor del atributo dexterity (20-100)

    Returns
    -------
    float
        Factor de precisión (>0), menor valor = mayor precisión

    Notes
    -----
    Este valor se usa como sigma/step size en mutaciones gaussianas.
    MENOR valor = MAYOR precisión (ajustes más finos).
    Alta dexterity -> precision baja (valor numérico) -> cambios pequeños.

    Examples
    --------
    >>> get_dexterity_precision(20)  # Baja dexterity = alta imprecisión
    1.0
    >>> get_dexterity_precision(100)  # Alta dexterity = baja imprecisión
    0.1
    """
    # Invertir: alta dexterity -> bajo sigma
    normalized = (dexterity - ATTRIBUTE_MIN) / (ATTRIBUTE_MAX - ATTRIBUTE_MIN)
    # Rango [0.1, 1.0]: nunca llegar a 0 para evitar divisiones por cero
    return 1.0 - (normalized * 0.9)


def get_luck_probability_boost(luck: float) -> float:
    """
    Calcular boost de probabilidad por suerte.

    Parameters
    ----------
    luck : float
        Valor del atributo luck (20-100)

    Returns
    -------
    float
        Boost de probabilidad en rango [0, 0.5]

    Notes
    -----
    Este boost se suma a probabilidades de eventos favorables:
    - Probabilidad de ser seleccionado para reproducción
    - Probabilidad de recibir mejor individuo en cruce
    - Probabilidad de mutación beneficiosa

    Limitado a 0.5 para evitar que luck domine completamente.

    Examples
    --------
    >>> get_luck_probability_boost(20)
    0.0
    >>> get_luck_probability_boost(100)
    0.5
    >>> get_luck_probability_boost(60)
    0.25
    """
    normalized = (luck - ATTRIBUTE_MIN) / (ATTRIBUTE_MAX - ATTRIBUTE_MIN)
    return normalized * 0.5


# =============================================================================
# VALIDACIÓN DE ATRIBUTOS
# =============================================================================

def clamp_attribute(value: float) -> float:
    """
    Limitar valor de atributo al rango válido [ATTRIBUTE_MIN, ATTRIBUTE_MAX].

    Parameters
    ----------
    value : float
        Valor a limitar

    Returns
    -------
    float
        Valor limitado al rango válido

    Examples
    --------
    >>> clamp_attribute(150)
    100
    >>> clamp_attribute(10)
    20
    >>> clamp_attribute(50)
    50
    """
    return max(ATTRIBUTE_MIN, min(ATTRIBUTE_MAX, value))


def is_valid_attribute_value(value: float) -> bool:
    """
    Verificar si un valor está en el rango válido de atributos.

    Parameters
    ----------
    value : float
        Valor a verificar

    Returns
    -------
    bool
        True si el valor está en [ATTRIBUTE_MIN, ATTRIBUTE_MAX]

    Examples
    --------
    >>> is_valid_attribute_value(50)
    True
    >>> is_valid_attribute_value(150)
    False
    >>> is_valid_attribute_value(10)
    False
    """
    return ATTRIBUTE_MIN <= value <= ATTRIBUTE_MAX


# =============================================================================
# CATEGORIZACIÓN DE ATRIBUTOS
# =============================================================================

def get_attribute_category(value: float) -> str:
    """
    Categorizar valor de atributo como 'low', 'medium', o 'high'.

    Parameters
    ----------
    value : float
        Valor del atributo

    Returns
    -------
    str
        Categoría: 'low' (<40), 'medium' (40-70), 'high' (>70)

    Examples
    --------
    >>> get_attribute_category(30)
    'low'
    >>> get_attribute_category(50)
    'medium'
    >>> get_attribute_category(90)
    'high'
    """
    if value < 40:
        return 'low'
    elif value <= 70:
        return 'medium'
    else:
        return 'high'


def get_dominant_attribute_from_dict(attributes: Dict[str, float]) -> str:
    """
    Identificar el atributo con mayor valor en un diccionario.

    Parameters
    ----------
    attributes : Dict[str, float]
        Diccionario con atributos RPG

    Returns
    -------
    str
        Nombre del atributo dominante

    Examples
    --------
    >>> attrs = {'strength': 90, 'wisdom': 40, 'endurance': 50,
    ...          'dexterity': 45, 'luck': 35}
    >>> get_dominant_attribute_from_dict(attrs)
    'strength'
    """
    return max(attributes, key=attributes.get)


# =============================================================================
# DISTRIBUCIÓN DE ATRIBUTOS
# =============================================================================

def distribute_points_randomly(
    attributes: Dict[str, float],
    points: int
) -> Dict[str, float]:
    """
    Distribuir puntos aleatoriamente entre atributos.

    Parameters
    ----------
    attributes : Dict[str, float]
        Diccionario con atributos actuales
    points : int
        Número de puntos a distribuir

    Returns
    -------
    Dict[str, float]
        Diccionario con atributos actualizados

    Notes
    -----
    - Los atributos están limitados a ATTRIBUTE_MAX (100)
    - Si un atributo alcanza 100, el punto se pierde
    - Modifica el diccionario in-place y también lo retorna

    Examples
    --------
    >>> attrs = {'strength': 50, 'wisdom': 50, 'endurance': 50,
    ...          'dexterity': 50, 'luck': 50}
    >>> result = distribute_points_randomly(attrs, 10)
    >>> sum(result.values()) > 250  # Debe aumentar
    True
    """
    for _ in range(points):
        # Elegir atributo aleatorio
        attr = random.choice(ATTRIBUTE_NAMES)

        # Incrementar si no ha alcanzado el máximo
        if attributes[attr] < ATTRIBUTE_MAX:
            attributes[attr] = min(ATTRIBUTE_MAX, attributes[attr] + 1)

    return attributes


def create_balanced_attributes() -> Dict[str, float]:
    """
    Crear diccionario de atributos balanceados (~50 cada uno).

    Returns
    -------
    Dict[str, float]
        Diccionario con atributos balanceados

    Notes
    -----
    Útil para crear soluciones de "tipo equilibrado" o para testing.
    Cada atributo se inicializa cerca de 50 con pequeña variación.

    Examples
    --------
    >>> attrs = create_balanced_attributes()
    >>> len(attrs)
    5
    >>> all(45 <= v <= 55 for v in attrs.values())
    True
    """
    attributes = {}
    for attr in ATTRIBUTE_NAMES:
        # 50 ± 2.5 para crear pequeña variación
        attributes[attr] = random.uniform(47.5, 52.5)

    return attributes


# =============================================================================
# COMPARACIÓN DE ATRIBUTOS
# =============================================================================

def compare_attribute_profiles(
    profile1: Dict[str, float],
    profile2: Dict[str, float]
) -> float:
    """
    Comparar similitud entre dos perfiles de atributos.

    Parameters
    ----------
    profile1 : Dict[str, float]
        Primer perfil de atributos
    profile2 : Dict[str, float]
        Segundo perfil de atributos

    Returns
    -------
    float
        Similitud en rango [0, 1], donde 1 = idénticos

    Notes
    -----
    Usa distancia euclidiana normalizada invertida:
    similarity = 1 - (distance / max_possible_distance)

    Examples
    --------
    >>> p1 = {'strength': 90, 'wisdom': 30, 'endurance': 50,
    ...       'dexterity': 40, 'luck': 35}
    >>> p2 = {'strength': 30, 'wisdom': 90, 'endurance': 50,
    ...       'dexterity': 40, 'luck': 35}
    >>> similarity = compare_attribute_profiles(p1, p2)
    >>> 0 <= similarity <= 1
    True
    >>> similarity < 0.8  # No muy similares
    True
    """
    # Calcular distancia euclidiana
    distance_squared = 0.0
    for attr in ATTRIBUTE_NAMES:
        diff = profile1[attr] - profile2[attr]
        distance_squared += diff * diff

    distance = distance_squared ** 0.5

    # Distancia máxima posible: todos los atributos difieren en 80
    # (de 20 a 100 o viceversa)
    max_distance = (80 * 80 * 5) ** 0.5  # sqrt(5 * 80^2)

    # Normalizar y convertir a similitud
    similarity = 1.0 - (distance / max_distance)

    return similarity


def calculate_attribute_diversity(attributes: Dict[str, float]) -> float:
    """
    Calcular diversidad (desviación estándar) de atributos.

    Parameters
    ----------
    attributes : Dict[str, float]
        Diccionario con atributos

    Returns
    -------
    float
        Diversidad (desviación estándar de los valores)

    Notes
    -----
    Mayor diversidad indica especialización (algunos atributos muy altos,
    otros muy bajos). Baja diversidad indica balance.

    Examples
    --------
    >>> uniform = {'strength': 50, 'wisdom': 50, 'endurance': 50,
    ...            'dexterity': 50, 'luck': 50}
    >>> diverse = {'strength': 20, 'wisdom': 100, 'endurance': 40,
    ...            'dexterity': 80, 'luck': 30}
    >>> div_uniform = calculate_attribute_diversity(uniform)
    >>> div_diverse = calculate_attribute_diversity(diverse)
    >>> div_diverse > div_uniform
    True
    """
    values = [attributes[attr] for attr in ATTRIBUTE_NAMES]

    # Calcular media
    mean = sum(values) / len(values)

    # Calcular varianza
    variance = sum((v - mean) ** 2 for v in values) / len(values)

    # Desviación estándar
    std_dev = variance ** 0.5

    return std_dev
