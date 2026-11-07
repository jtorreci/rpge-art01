"""
Sistema de experiencia (XP) para RPG-META.

Gestiona múltiples fuentes de XP, modificadores, eventos especiales
y tracking detallado de experiencia ganada.
"""
from enum import Enum
from typing import Dict, Optional


# =============================================================================
# CONSTANTES Y ENUMS
# =============================================================================

class XPSource(Enum):
    """Fuentes de experiencia."""
    DOMINANCE = 'dominance'
    IMPROVEMENT = 'improvement'
    SURVIVAL = 'survival'
    BREEDING = 'breeding'
    PARETO_FRONT = 'pareto_front'


# Cantidades base de XP por fuente
XP_AMOUNTS = {
    'dominance': 20,        # Dominar otra solución
    'improvement': 30,      # Mejorar objetivos
    'survival': 10,         # Sobrevivir generación
    'breeding': 25,         # Ser seleccionado para reproducción
    'pareto_front': 50,     # Estar en frente de Pareto
}


# =============================================================================
# CÁLCULO DE XP
# =============================================================================

def calculate_dominance_xp() -> int:
    """
    Calcular XP por dominar otra solución.

    Returns
    -------
    int
        XP ganado por dominancia

    Notes
    -----
    Se otorga cuando una solución domina a otra en comparación de Pareto.

    Examples
    --------
    >>> calculate_dominance_xp()
    20
    """
    return XP_AMOUNTS['dominance']


def calculate_improvement_xp(improvement_ratio: float) -> float:
    """
    Calcular XP por mejorar objetivos.

    Parameters
    ----------
    improvement_ratio : float
        Ratio de mejora (0.0 a 1.0+)
        Ejemplo: 0.1 = mejora del 10%

    Returns
    -------
    float
        XP ganado por mejora

    Notes
    -----
    Mayor mejora = más XP. La fórmula escala linealmente con el ratio:
    XP = base_xp * (1 + improvement_ratio)

    Examples
    --------
    >>> calculate_improvement_xp(0.0)  # Sin mejora
    30.0
    >>> calculate_improvement_xp(0.1)  # Mejora 10%
    33.0
    >>> calculate_improvement_xp(0.5)  # Mejora 50%
    45.0
    """
    base_xp = XP_AMOUNTS['improvement']
    return base_xp * (1.0 + improvement_ratio)


def calculate_survival_xp(generations: int) -> float:
    """
    Calcular XP por sobrevivir generaciones.

    Parameters
    ----------
    generations : int
        Número de generaciones sobrevividas

    Returns
    -------
    float
        XP ganado por supervivencia

    Notes
    -----
    XP aumenta con cada generación pero con rendimientos decrecientes
    para evitar que soluciones estancadas ganen XP infinito.
    Fórmula: base_xp * sqrt(generations)

    Examples
    --------
    >>> calculate_survival_xp(1)
    10.0
    >>> calculate_survival_xp(4)
    20.0
    >>> calculate_survival_xp(9)
    30.0
    """
    base_xp = XP_AMOUNTS['survival']
    return base_xp * (generations ** 0.5)


def calculate_breeding_xp() -> int:
    """
    Calcular XP por ser seleccionado para reproducción.

    Returns
    -------
    int
        XP ganado por breeding

    Notes
    -----
    Se otorga cada vez que la solución es elegida como padre/madre
    en operadores de cruce.

    Examples
    --------
    >>> calculate_breeding_xp()
    25
    """
    return XP_AMOUNTS['breeding']


def calculate_pareto_front_xp() -> int:
    """
    Calcular XP por estar en el frente de Pareto.

    Returns
    -------
    int
        XP ganado por estar en frente óptimo

    Notes
    -----
    Es la mayor recompensa de XP porque indica solución no dominada.
    Se otorga una vez por generación si la solución está en el frente.

    Examples
    --------
    >>> calculate_pareto_front_xp()
    50
    """
    return XP_AMOUNTS['pareto_front']


# =============================================================================
# MODIFICADORES DE XP
# =============================================================================

def apply_attribute_modifier(base_xp: float, wisdom: float) -> float:
    """
    Aplicar modificador de XP basado en atributos.

    Parameters
    ----------
    base_xp : float
        XP base antes del modificador
    wisdom : float
        Valor del atributo wisdom (20-100)

    Returns
    -------
    float
        XP modificado

    Notes
    -----
    Mayor wisdom aumenta la ganancia de XP (aprendizaje más rápido).
    Fórmula: XP * (1 + wisdom_modifier * 0.5)
    Rango de multiplicador: [1.0, 1.5]

    Examples
    --------
    >>> apply_attribute_modifier(100, wisdom=20)  # Wisdom mínimo
    100.0
    >>> apply_attribute_modifier(100, wisdom=100)  # Wisdom máximo
    150.0
    >>> apply_attribute_modifier(100, wisdom=60)   # Wisdom medio
    125.0
    """
    # Normalizar wisdom a [0, 1]
    wisdom_normalized = (wisdom - 20) / 80

    # Aplicar modificador (hasta +50% de XP)
    multiplier = 1.0 + (wisdom_normalized * 0.5)

    return base_xp * multiplier


def apply_level_penalty(base_xp: float, level: int) -> float:
    """
    Aplicar penalización por nivel alto.

    Parameters
    ----------
    base_xp : float
        XP base antes de la penalización
    level : int
        Nivel actual de la solución

    Returns
    -------
    float
        XP con penalización aplicada

    Notes
    -----
    Niveles más altos obtienen menos XP para ralentizar progresión
    y mantener equilibrio. Fórmula: XP / (1 + level * 0.05)

    La penalización nunca reduce XP a menos del 20% del original.

    Examples
    --------
    >>> apply_level_penalty(100, level=1)
    95.23809523809524
    >>> apply_level_penalty(100, level=10)
    66.66666666666666
    >>> apply_level_penalty(100, level=20)
    50.0
    """
    penalty_factor = 1.0 + (level * 0.05)

    # Aplicar penalización
    penalized_xp = base_xp / penalty_factor

    # Nunca reducir a menos del 20% del XP original
    min_xp = base_xp * 0.2
    return max(penalized_xp, min_xp)


# =============================================================================
# EVENTOS ESPECIALES
# =============================================================================

def apply_bonus_event(base_xp: float, multiplier: float = 2.0) -> float:
    """
    Aplicar bonus de XP por evento especial.

    Parameters
    ----------
    base_xp : float
        XP base
    multiplier : float, optional
        Multiplicador del bonus (default: 2.0)

    Returns
    -------
    float
        XP con bonus aplicado

    Examples
    --------
    >>> apply_bonus_event(100, multiplier=2.0)
    200.0
    >>> apply_bonus_event(50, multiplier=1.5)
    75.0
    """
    return base_xp * multiplier


def calculate_critical_success_xp(base_xp: float) -> float:
    """
    Calcular XP extra por éxito crítico.

    Parameters
    ----------
    base_xp : float
        XP base de la acción

    Returns
    -------
    float
        XP con bonus de crítico (+50%)

    Notes
    -----
    Un crítico puede ocurrir en eventos de alta suerte o
    mejoras excepcionales. Otorga +50% de XP.

    Examples
    --------
    >>> calculate_critical_success_xp(100)
    150.0
    """
    return base_xp * 1.5


def calculate_first_pareto_bonus() -> int:
    """
    Calcular bonus por primera vez en frente de Pareto.

    Returns
    -------
    int
        Bonus de XP one-time

    Notes
    -----
    Se otorga solo la primera vez que una solución alcanza
    el frente de Pareto (milestone achievement).

    Examples
    --------
    >>> calculate_first_pareto_bonus()
    100
    """
    return 100


# =============================================================================
# XP TRACKER
# =============================================================================

class XPTracker:
    """
    Rastreador de experiencia ganada por fuente.

    Attributes
    ----------
    total_xp : float
        XP total acumulado
    xp_by_source : Dict[str, float]
        XP ganado por cada fuente
    first_pareto_achieved : bool
        Si ya se alcanzó el frente de Pareto

    Examples
    --------
    >>> tracker = XPTracker()
    >>> tracker.add_xp('dominance', 20)
    >>> tracker.add_xp('improvement', 30)
    >>> tracker.total_xp
    50.0
    """

    def __init__(self):
        """Inicializar tracker."""
        self.total_xp = 0.0
        self.xp_by_source: Dict[str, float] = {
            'dominance': 0.0,
            'improvement': 0.0,
            'survival': 0.0,
            'breeding': 0.0,
            'pareto_front': 0.0,
            'bonus': 0.0,
        }
        self.first_pareto_achieved = False

    def add_xp(self, source: str, amount: float) -> None:
        """
        Añadir XP de una fuente.

        Parameters
        ----------
        source : str
            Fuente de XP ('dominance', 'improvement', etc.)
        amount : float
            Cantidad de XP ganada
        """
        if source not in self.xp_by_source:
            self.xp_by_source[source] = 0.0

        self.xp_by_source[source] += amount
        self.total_xp += amount

    def get_xp_from_source(self, source: str) -> float:
        """
        Obtener XP ganado de una fuente específica.

        Parameters
        ----------
        source : str
            Nombre de la fuente

        Returns
        -------
        float
            XP acumulado de esa fuente
        """
        return self.xp_by_source.get(source, 0.0)

    def get_top_source(self) -> Optional[str]:
        """
        Identificar la fuente que más XP ha dado.

        Returns
        -------
        Optional[str]
            Nombre de la fuente principal, o None si no hay XP
        """
        if self.total_xp == 0:
            return None

        return max(self.xp_by_source, key=self.xp_by_source.get)

    def reset(self) -> None:
        """Reiniciar el tracker a valores iniciales."""
        self.total_xp = 0.0
        for source in self.xp_by_source:
            self.xp_by_source[source] = 0.0
        self.first_pareto_achieved = False

    def get_statistics(self) -> Dict:
        """
        Obtener estadísticas completas del tracker.

        Returns
        -------
        Dict
            Diccionario con total y desglose por fuente
        """
        return {
            'total': self.total_xp,
            'by_source': self.xp_by_source.copy(),
            'top_source': self.get_top_source(),
        }


# =============================================================================
# DECAIMIENTO DE XP (OPCIONAL)
# =============================================================================

def apply_xp_decay(
    current_xp: float,
    generations_inactive: int,
    decay_rate: float = 0.05
) -> float:
    """
    Aplicar decaimiento de XP por inactividad.

    Parameters
    ----------
    current_xp : float
        XP actual
    generations_inactive : int
        Generaciones sin actividad (sin mejora, sin dominancia, etc.)
    decay_rate : float, optional
        Tasa de decaimiento por generación (default: 0.05 = 5%)

    Returns
    -------
    float
        XP después del decaimiento

    Notes
    -----
    El decaimiento es exponencial: XP * (1 - decay_rate) ^ generations
    Nunca llega a 0, pero se acerca asintóticamente.

    Examples
    --------
    >>> apply_xp_decay(100, generations_inactive=0)
    100.0
    >>> apply_xp_decay(100, generations_inactive=5)
    77.37809374999999
    >>> apply_xp_decay(100, generations_inactive=10)
    59.873693923837896
    """
    if generations_inactive == 0:
        return current_xp

    # Decaimiento exponencial
    decay_factor = (1.0 - decay_rate) ** generations_inactive
    decayed_xp = current_xp * decay_factor

    # Nunca negativo
    return max(0.0, decayed_xp)


# =============================================================================
# UTILIDADES
# =============================================================================

def xp_to_level(total_xp: float) -> int:
    """
    Calcular nivel equivalente a cierta cantidad de XP.

    Parameters
    ----------
    total_xp : float
        XP total acumulado

    Returns
    -------
    int
        Nivel equivalente

    Notes
    -----
    Usa la fórmula estándar: nivel N requiere sum(i*100 for i in 1..N-1) XP
    Nivel 1: 0 XP
    Nivel 2: 100 XP
    Nivel 3: 300 XP (100 + 200)
    Nivel 4: 600 XP (100 + 200 + 300)

    Examples
    --------
    >>> xp_to_level(0)
    1
    >>> xp_to_level(100)
    2
    >>> xp_to_level(300)
    3
    """
    if total_xp < 0:
        return 1

    level = 1
    xp_needed = 0

    while xp_needed <= total_xp:
        xp_needed += level * 100
        if xp_needed <= total_xp:
            level += 1

    return level


def get_xp_progress_percentage(current_xp: float, xp_for_next: float) -> float:
    """
    Calcular porcentaje de progreso al siguiente nivel.

    Parameters
    ----------
    current_xp : float
        XP actual hacia el siguiente nivel
    xp_for_next : float
        XP total necesario para el siguiente nivel

    Returns
    -------
    float
        Porcentaje (0.0 a 100.0)

    Examples
    --------
    >>> get_xp_progress_percentage(50, 100)
    50.0
    >>> get_xp_progress_percentage(75, 100)
    75.0
    """
    if xp_for_next == 0:
        return 0.0

    return (current_xp / xp_for_next) * 100.0


def estimate_levels_from_xp(
    current_level: int,
    current_xp: float,
    xp_to_add: float
) -> int:
    """
    Estimar cuántos niveles se pueden ganar con cierto XP.

    Parameters
    ----------
    current_level : int
        Nivel actual
    current_xp : float
        XP actual hacia siguiente nivel
    xp_to_add : float
        XP que se va a añadir

    Returns
    -------
    int
        Número de niveles que se ganarán

    Examples
    --------
    >>> estimate_levels_from_xp(1, 0, 100)
    1
    >>> estimate_levels_from_xp(1, 0, 500)
    3
    """
    levels_gained = 0
    level = current_level
    xp = current_xp + xp_to_add

    while xp >= level * 100:
        xp -= level * 100
        level += 1
        levels_gained += 1

    return levels_gained
