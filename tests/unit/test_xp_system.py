"""
Tests unitarios para el sistema de experiencia (XP).

Siguiendo TDD: estos tests se escriben ANTES de implementar el módulo.
El sistema XP gestiona múltiples fuentes de experiencia y eventos especiales.
"""
import pytest


class TestXPConstants:
    """Tests de constantes del sistema XP."""

    def test_xp_sources_exist(self):
        """Debe tener definidas las fuentes de XP"""
        from core.xp_system import XPSource

        assert hasattr(XPSource, 'DOMINANCE')
        assert hasattr(XPSource, 'IMPROVEMENT')
        assert hasattr(XPSource, 'SURVIVAL')
        assert hasattr(XPSource, 'BREEDING')
        assert hasattr(XPSource, 'PARETO_FRONT')

    def test_xp_source_values(self):
        """Las fuentes de XP deben tener valores configurados"""
        from core.xp_system import XP_AMOUNTS

        assert 'dominance' in XP_AMOUNTS
        assert 'improvement' in XP_AMOUNTS
        assert 'survival' in XP_AMOUNTS
        assert 'breeding' in XP_AMOUNTS
        assert 'pareto_front' in XP_AMOUNTS

        # Todos deben ser valores positivos
        for amount in XP_AMOUNTS.values():
            assert amount > 0


class TestXPCalculation:
    """Tests de cálculo de XP."""

    def test_calculate_dominance_xp(self):
        """Debe calcular XP por dominar otra solución"""
        from core.xp_system import calculate_dominance_xp

        xp = calculate_dominance_xp()

        assert xp > 0
        assert isinstance(xp, (int, float))

    def test_calculate_improvement_xp(self):
        """Debe calcular XP por mejorar objetivos"""
        from core.xp_system import calculate_improvement_xp

        # Mejora pequeña
        xp_small = calculate_improvement_xp(improvement_ratio=0.01)

        # Mejora grande
        xp_large = calculate_improvement_xp(improvement_ratio=0.5)

        assert xp_large > xp_small
        assert xp_small > 0

    def test_calculate_survival_xp(self):
        """Debe calcular XP por sobrevivir generaciones"""
        from core.xp_system import calculate_survival_xp

        # Sobrevivir 1 generación
        xp_1 = calculate_survival_xp(generations=1)

        # Sobrevivir 10 generaciones
        xp_10 = calculate_survival_xp(generations=10)

        assert xp_10 > xp_1
        assert xp_1 > 0

    def test_calculate_breeding_xp(self):
        """Debe calcular XP por ser seleccionado para reproducción"""
        from core.xp_system import calculate_breeding_xp

        xp = calculate_breeding_xp()

        assert xp > 0
        assert isinstance(xp, (int, float))

    def test_calculate_pareto_front_xp(self):
        """Debe calcular XP por estar en el frente de Pareto"""
        from core.xp_system import calculate_pareto_front_xp

        xp = calculate_pareto_front_xp()

        assert xp > 0
        assert isinstance(xp, (int, float))

    def test_pareto_front_xp_is_highest(self):
        """XP del frente de Pareto debe ser el más alto"""
        from core.xp_system import (
            calculate_pareto_front_xp,
            calculate_dominance_xp,
            calculate_breeding_xp
        )

        pareto_xp = calculate_pareto_front_xp()
        dominance_xp = calculate_dominance_xp()
        breeding_xp = calculate_breeding_xp()

        assert pareto_xp >= dominance_xp
        assert pareto_xp >= breeding_xp


class TestXPModifiers:
    """Tests de modificadores de XP."""

    def test_apply_attribute_modifier(self):
        """Debe aplicar modificador basado en atributos"""
        from core.xp_system import apply_attribute_modifier

        base_xp = 100
        high_wisdom = 90
        low_wisdom = 30

        xp_high = apply_attribute_modifier(base_xp, wisdom=high_wisdom)
        xp_low = apply_attribute_modifier(base_xp, wisdom=low_wisdom)

        # Mayor wisdom = más XP
        assert xp_high > xp_low
        assert xp_low >= base_xp  # Nunca penalizar

    def test_apply_level_penalty(self):
        """Debe aplicar penalización por nivel alto"""
        from core.xp_system import apply_level_penalty

        base_xp = 100
        low_level = 1
        high_level = 10

        xp_low_level = apply_level_penalty(base_xp, level=low_level)
        xp_high_level = apply_level_penalty(base_xp, level=high_level)

        # Niveles altos obtienen menos XP
        assert xp_high_level < xp_low_level
        assert xp_high_level > 0  # Nunca llegar a 0


class TestXPEvents:
    """Tests de eventos especiales de XP."""

    def test_xp_bonus_event(self):
        """Debe poder otorgar bonus de XP especiales"""
        from core.xp_system import apply_bonus_event

        base_xp = 100
        bonus_multiplier = 2.0

        xp_with_bonus = apply_bonus_event(base_xp, multiplier=bonus_multiplier)

        assert xp_with_bonus == base_xp * bonus_multiplier

    def test_critical_success_xp(self):
        """Debe otorgar XP extra por éxito crítico"""
        from core.xp_system import calculate_critical_success_xp

        base_xp = 100
        critical_xp = calculate_critical_success_xp(base_xp)

        assert critical_xp > base_xp

    def test_first_pareto_bonus(self):
        """Debe otorgar bonus por primera vez en frente de Pareto"""
        from core.xp_system import calculate_first_pareto_bonus

        bonus = calculate_first_pareto_bonus()

        assert bonus > 0


class TestXPTracker:
    """Tests del tracker de XP."""

    def test_xp_tracker_initialization(self):
        """Debe poder crear tracker de XP"""
        from core.xp_system import XPTracker

        tracker = XPTracker()

        assert tracker is not None
        assert hasattr(tracker, 'total_xp')
        assert tracker.total_xp == 0

    def test_track_xp_gain(self):
        """Debe rastrear ganancia de XP por fuente"""
        from core.xp_system import XPTracker

        tracker = XPTracker()

        tracker.add_xp('dominance', 50)
        tracker.add_xp('improvement', 30)

        assert tracker.total_xp == 80

    def test_get_xp_by_source(self):
        """Debe poder obtener XP ganado por cada fuente"""
        from core.xp_system import XPTracker

        tracker = XPTracker()

        tracker.add_xp('dominance', 50)
        tracker.add_xp('dominance', 25)
        tracker.add_xp('improvement', 30)

        dominance_xp = tracker.get_xp_from_source('dominance')
        improvement_xp = tracker.get_xp_from_source('improvement')

        assert dominance_xp == 75
        assert improvement_xp == 30

    def test_get_most_valuable_source(self):
        """Debe identificar la fuente que más XP ha dado"""
        from core.xp_system import XPTracker

        tracker = XPTracker()

        tracker.add_xp('dominance', 50)
        tracker.add_xp('improvement', 100)
        tracker.add_xp('survival', 30)

        top_source = tracker.get_top_source()

        assert top_source == 'improvement'

    def test_reset_tracker(self):
        """Debe poder reiniciar el tracker"""
        from core.xp_system import XPTracker

        tracker = XPTracker()

        tracker.add_xp('dominance', 50)
        tracker.reset()

        assert tracker.total_xp == 0


class TestXPDecay:
    """Tests de decaimiento de XP (opcional)."""

    def test_apply_xp_decay(self):
        """Debe aplicar decaimiento de XP por inactividad"""
        from core.xp_system import apply_xp_decay

        current_xp = 100
        generations_inactive = 5

        decayed_xp = apply_xp_decay(current_xp, generations_inactive)

        assert decayed_xp < current_xp
        assert decayed_xp >= 0

    def test_no_decay_when_active(self):
        """No debe haber decaimiento si hay actividad reciente"""
        from core.xp_system import apply_xp_decay

        current_xp = 100
        generations_inactive = 0

        decayed_xp = apply_xp_decay(current_xp, generations_inactive)

        assert decayed_xp == current_xp

    def test_decay_never_negative(self):
        """Decaimiento no debe llevar XP a valores negativos"""
        from core.xp_system import apply_xp_decay

        current_xp = 50
        generations_inactive = 1000  # Muchas generaciones

        decayed_xp = apply_xp_decay(current_xp, generations_inactive)

        assert decayed_xp >= 0


class TestXPIntegration:
    """Tests de integración del sistema XP."""

    def test_complete_xp_cycle(self):
        """Debe poder completar ciclo completo de XP"""
        from core.xp_system import (
            XPTracker,
            calculate_dominance_xp,
            calculate_improvement_xp,
            apply_attribute_modifier
        )

        tracker = XPTracker()

        # Ganar XP por dominar
        dominance_xp = calculate_dominance_xp()
        tracker.add_xp('dominance', dominance_xp)

        # Ganar XP por mejorar
        improvement_xp = calculate_improvement_xp(improvement_ratio=0.1)
        improvement_xp = apply_attribute_modifier(improvement_xp, wisdom=80)
        tracker.add_xp('improvement', improvement_xp)

        assert tracker.total_xp > 0

    def test_xp_tracker_statistics(self):
        """Debe poder generar estadísticas de XP"""
        from core.xp_system import XPTracker

        tracker = XPTracker()

        tracker.add_xp('dominance', 50)
        tracker.add_xp('improvement', 100)
        tracker.add_xp('survival', 30)
        tracker.add_xp('pareto_front', 200)

        stats = tracker.get_statistics()

        assert 'total' in stats
        assert 'by_source' in stats
        assert stats['total'] == 380


class TestXPUtilities:
    """Tests de utilidades del sistema XP."""

    def test_xp_to_level_conversion(self):
        """Debe calcular nivel equivalente a cierta cantidad de XP"""
        from core.xp_system import xp_to_level

        level_1 = xp_to_level(0)
        level_2 = xp_to_level(100)
        level_5 = xp_to_level(1000)

        assert level_1 == 1
        assert level_2 >= 1
        assert level_5 > level_2

    def test_xp_percentage_to_next_level(self):
        """Debe calcular porcentaje de progreso al siguiente nivel"""
        from core.xp_system import get_xp_progress_percentage

        # 50 XP de 100 necesarios = 50%
        percentage = get_xp_progress_percentage(
            current_xp=50,
            xp_for_next=100
        )

        assert percentage == 50.0

    def test_estimate_levels_from_xp(self):
        """Debe estimar cuántos niveles se pueden ganar con cierto XP"""
        from core.xp_system import estimate_levels_from_xp

        current_level = 1
        current_xp = 0
        xp_to_add = 500

        levels_gained = estimate_levels_from_xp(
            current_level=current_level,
            current_xp=current_xp,
            xp_to_add=xp_to_add
        )

        assert levels_gained >= 1
