"""
Clase RPGSolution: Solución con atributos RPG.

Extiende la funcionalidad básica de soluciones de optimización
añadiendo atributos tipo juego de rol que evolucionan.
"""
import random
from typing import Dict, Tuple, List, Optional, Any


class RPGSolution:
    """
    Solución con atributos RPG (Role-Playing Game).

    Esta clase representa una solución de optimización enriquecida con
    atributos tipo personaje de RPG que afectan su comportamiento durante
    la evolución del algoritmo.

    Attributes
    ----------
    problem : object
        Problema de optimización a resolver
    strength : float
        Fuerza (20-100): Capacidad de hacer cambios grandes/agresivos
    wisdom : float
        Sabiduría (20-100): Uso de información histórica y del frente
    endurance : float
        Resistencia (20-100): Capacidad de sobrevivir sin mejora
    dexterity : float
        Destreza (20-100): Precisión en ajustes finos
    luck : float
        Suerte (20-100): Sesgo aleatorio favorable
    level : int
        Nivel del personaje (empieza en 1)
    xp : int
        Puntos de experiencia acumulados
    age : int
        Edad (iteraciones sin mejora)

    Examples
    --------
    >>> problem = create_problem()
    >>> sol = RPGSolution(problem)
    >>> sol.level
    1
    >>> sol.gain_xp(100)
    >>> sol.level
    2
    """

    def __init__(self, problem):
        """
        Inicializar solución con atributos RPG.

        Parameters
        ----------
        problem : object
            Problema de optimización
        """
        self.problem = problem
        self._initialize_rpg_attributes()

    def _initialize_rpg_attributes(self) -> None:
        """
        Inicializar atributos RPG en rango [20, 80].

        Los atributos se distribuyen aleatoriamente para crear
        diversidad en la población inicial.
        """
        self.strength = random.uniform(20, 80)
        self.wisdom = random.uniform(20, 80)
        self.endurance = random.uniform(20, 80)
        self.dexterity = random.uniform(20, 80)
        self.luck = random.uniform(20, 80)

        # Sistema de experiencia
        self.level = 1
        self.xp = 0

        # Edad (iteraciones sin mejora)
        self.age = 0

        # Atributos compatibles con Platypus
        self.variables: List[Any] = []
        self.objectives: List[float] = []
        self.constraints: List[float] = []
        self.constraint_violation: float = 0.0
        self.evaluated = False

    def gain_xp(self, amount: int) -> None:
        """
        Ganar experiencia y subir de nivel si corresponde.

        Parameters
        ----------
        amount : int
            Cantidad de XP ganada

        Notes
        -----
        Si XP acumulado supera el umbral, se sube de nivel automáticamente
        y se distribuyen puntos de atributo.

        Examples
        --------
        >>> sol.gain_xp(100)
        >>> sol.level
        2
        """
        self.xp += amount

        # Subir niveles mientras haya XP suficiente
        while self.xp >= self.xp_for_next_level():
            self.level_up()

    def xp_for_next_level(self) -> int:
        """
        Calcular XP requerido para siguiente nivel.

        Returns
        -------
        int
            XP necesario para subir de nivel

        Notes
        -----
        Fórmula: XP_requerido = nivel_actual * 100
        Esto hace que cada nivel sea más difícil de alcanzar.

        Examples
        --------
        >>> sol.level = 1
        >>> sol.xp_for_next_level()
        100
        >>> sol.level = 5
        >>> sol.xp_for_next_level()
        500
        """
        return self.level * 100

    def level_up(self) -> None:
        """
        Subir de nivel y distribuir puntos de atributo.

        Distribuye 5 puntos aleatorios entre los atributos,
        respetando el tope de 100 por atributo.

        Notes
        -----
        - XP sobrante se mantiene para el siguiente nivel
        - Cada nivel otorga +5 puntos de atributo totales
        - Los puntos se distribuyen aleatoriamente
        """
        # Restar XP usado
        self.xp -= self.xp_for_next_level()

        # Subir nivel
        self.level += 1

        # Distribuir 5 puntos de atributo
        self._distribute_attribute_points(5)

    def _distribute_attribute_points(self, points: int) -> None:
        """
        Distribuir puntos aleatoriamente en atributos.

        Parameters
        ----------
        points : int
            Número de puntos a distribuir

        Notes
        -----
        Los atributos están limitados a 100 máximo.
        """
        attributes = ['strength', 'wisdom', 'endurance', 'dexterity', 'luck']

        for _ in range(points):
            # Elegir atributo aleatorio
            attr = random.choice(attributes)
            current = getattr(self, attr)

            # Incrementar si no ha alcanzado el máximo
            if current < 100:
                setattr(self, attr, min(100, current + 1))

    def get_attribute_sum(self) -> float:
        """
        Obtener suma total de atributos.

        Returns
        -------
        float
            Suma de todos los atributos RPG

        Examples
        --------
        >>> sol.get_attribute_sum()
        250.5
        """
        return (self.strength + self.wisdom + self.endurance +
                self.dexterity + self.luck)

    def get_dominant_attribute(self) -> str:
        """
        Identificar el atributo dominante (más alto).

        Returns
        -------
        str
            Nombre del atributo con mayor valor

        Examples
        --------
        >>> sol.strength = 90
        >>> sol.get_dominant_attribute()
        'strength'
        """
        attributes = {
            'strength': self.strength,
            'wisdom': self.wisdom,
            'endurance': self.endurance,
            'dexterity': self.dexterity,
            'luck': self.luck
        }

        return max(attributes, key=attributes.get)

    def get_combat_power(self) -> float:
        """
        Calcular poder de combate total.

        El poder de combate combina nivel y atributos para
        determinar la "fuerza" general de la solución en
        selección por torneo.

        Returns
        -------
        float
            Poder de combate total

        Notes
        -----
        Fórmula: nivel * 10 + promedio_atributos
        """
        avg_attributes = self.get_attribute_sum() / 5
        return self.level * 10 + avg_attributes

    def reset_xp(self) -> None:
        """
        Reiniciar XP a cero.

        Útil para experimentos o reinicializaciones.
        El nivel no cambia.
        """
        self.xp = 0

    def increment_age(self) -> None:
        """Incrementar edad en 1."""
        self.age += 1

    def reset_age(self) -> None:
        """Reiniciar edad a 0."""
        self.age = 0

    def __str__(self) -> str:
        """
        Representación legible de la solución.

        Returns
        -------
        str
            String descriptivo
        """
        dominant = self.get_dominant_attribute()
        return (
            f"RPGSolution(level={self.level}, "
            f"dominant={dominant}={getattr(self, dominant):.1f}, "
            f"power={self.get_combat_power():.1f})"
        )

    def __repr__(self) -> str:
        """
        Representación técnica de la solución.

        Returns
        -------
        str
            String técnico con todos los detalles
        """
        return (
            f"RPGSolution(level={self.level}, xp={self.xp}, "
            f"str={self.strength:.1f}, wis={self.wisdom:.1f}, "
            f"end={self.endurance:.1f}, dex={self.dexterity:.1f}, "
            f"luck={self.luck:.1f}, age={self.age})"
        )

    # =========================================================================
    # MÉTODOS COMPATIBLES CON PLATYPUS
    # =========================================================================

    def evaluate(self, problem: Any) -> None:
        """
        Evaluar la solución usando el problema.

        Parameters
        ----------
        problem : object
            Problema de optimización con método evaluate()

        Notes
        -----
        Este método es compatible con la interfaz de Platypus.
        Llama a problem.evaluate(self) para calcular objetivos.
        """
        if hasattr(problem, 'evaluate'):
            problem.evaluate(self)
            self.evaluated = True

    def copy(self) -> 'RPGSolution':
        """
        Crear copia profunda de la solución.

        Returns
        -------
        RPGSolution
            Nueva solución con los mismos valores

        Notes
        -----
        Copia todos los atributos RPG y de optimización.
        Útil para operadores genéticos que necesitan preservar el original.
        """
        new_solution = RPGSolution(self.problem)

        # Copiar atributos RPG
        new_solution.strength = self.strength
        new_solution.wisdom = self.wisdom
        new_solution.endurance = self.endurance
        new_solution.dexterity = self.dexterity
        new_solution.luck = self.luck

        # Copiar experiencia y nivel
        new_solution.level = self.level
        new_solution.xp = self.xp
        new_solution.age = self.age

        # Copiar atributos de optimización
        new_solution.variables = self.variables.copy() if self.variables else []
        new_solution.objectives = self.objectives.copy() if self.objectives else []
        new_solution.constraints = self.constraints.copy() if self.constraints else []
        new_solution.constraint_violation = self.constraint_violation
        new_solution.evaluated = self.evaluated

        return new_solution

    def violates_constraints(self) -> bool:
        """
        Verificar si la solución viola restricciones.

        Returns
        -------
        bool
            True si hay violación de restricciones

        Notes
        -----
        Compatible con interfaz Platypus para manejo de restricciones.
        """
        return self.constraint_violation > 0.0

    def feasible(self) -> bool:
        """
        Verificar si la solución es factible.

        Returns
        -------
        bool
            True si la solución no viola restricciones

        Notes
        -----
        Método de conveniencia, inverso de violates_constraints().
        """
        return not self.violates_constraints()

    # =========================================================================
    # MÉTODOS DE CLASE RPG
    # =========================================================================

    def get_attributes(self) -> Dict[str, float]:
        """
        Obtener diccionario con todos los atributos RPG.

        Returns
        -------
        Dict[str, float]
            Diccionario con los 5 atributos

        Examples
        --------
        >>> sol = RPGSolution(problem)
        >>> attrs = sol.get_attributes()
        >>> attrs['strength']
        65.0
        """
        return {
            'strength': self.strength,
            'wisdom': self.wisdom,
            'endurance': self.endurance,
            'dexterity': self.dexterity,
            'luck': self.luck
        }

    def get_rpg_class(self) -> str:
        """
        Obtener clase RPG según perfil de atributos.

        Returns
        -------
        str
            Nombre de la clase ('warrior', 'monk', 'rogue', 'scout', 'paladin')

        Notes
        -----
        La clase se asigna según los dos atributos dominantes, siguiendo los
        cinco sectores del glifo de perfil (formalismo art01, S3.7):
        - Warrior: Strength + Endurance
        - Monk: Endurance + Dexterity
        - Rogue: Dexterity + Luck
        - Scout: Luck + Wisdom
        - Paladin: Wisdom + Strength

        Examples
        --------
        >>> sol.strength = 90
        >>> sol.endurance = 85
        >>> sol.get_rpg_class()
        'warrior'
        """
        from core.rpg_classes import assign_rpg_class

        attributes = {
            'strength': self.strength,
            'wisdom': self.wisdom,
            'endurance': self.endurance,
            'dexterity': self.dexterity,
            'luck': self.luck
        }

        return assign_rpg_class(attributes)

    def get_class_bonus(self) -> Dict:
        """
        Obtener los rasgos de la clase actual.

        Returns
        -------
        Dict
            Diccionario con la descripción de la clase; sin valores numéricos

        Notes
        -----
        Las clases no llevan multiplicadores (formalismo art01, S3.7): el
        comportamiento lo fijan los atributos, no la etiqueta.

        Examples
        --------
        >>> sol.get_rpg_class()  # 'warrior'
        >>> bonus = sol.get_class_bonus()
        >>> bonus['description']
        'Exploración agresiva'
        """
        from core.rpg_classes import get_class_bonus

        rpg_class = self.get_rpg_class()
        return get_class_bonus(rpg_class)
