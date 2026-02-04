"""Trigger evaluation logic extracted from binary_sensor.py.

This module handles all trigger type evaluation in a testable way.
"""
import logging
from typing import Dict, Any, Optional
from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import Template

from ..const import (
    TRIGGER_TYPE_SIMPLE,
    TRIGGER_TYPE_TEMPLATE,
    TRIGGER_TYPE_LOGICAL,
    # TRIGGER_TYPE_COMBINED removed in Phase 2
    COMP_EQ, COMP_NE, COMP_LT, COMP_LTE, COMP_GT, COMP_GTE,
)

_LOGGER = logging.getLogger(__name__)


class TriggerEvaluator:
    """Evaluates alert triggers."""
    
    def __init__(self, hass: HomeAssistant):
        """Initialize the trigger evaluator."""
        self.hass = hass
    
    async def evaluate(self, config: Dict[str, Any]) -> bool:
        """Evaluate a trigger configuration.
        
        Args:
            config: Trigger configuration dictionary containing:
                - trigger_type: Type of trigger (simple, template, logical, combined)
                - Additional fields based on trigger type
        
        Returns:
            True if trigger condition is met, False otherwise
        """
        trigger_type = config.get("trigger_type", TRIGGER_TYPE_SIMPLE)
        
        if trigger_type == TRIGGER_TYPE_SIMPLE:
            return self._evaluate_simple(config)
        elif trigger_type == TRIGGER_TYPE_TEMPLATE:
            return await self._evaluate_template(config)
        elif trigger_type == TRIGGER_TYPE_LOGICAL:
            return self._evaluate_logical(config)
        # TRIGGER_TYPE_COMBINED removed in Phase 2 - was redundant with logical
        else:
            _LOGGER.warning(f"Unknown trigger type: {trigger_type}")
            return False
    
    def _evaluate_simple(self, config: Dict[str, Any]) -> bool:
        """Evaluate simple entity state trigger."""
        entity_id = config.get("entity_id")
        trigger_state = config.get("trigger_state")
        
        if not entity_id or trigger_state is None:
            return False
        
        state = self.hass.states.get(entity_id)
        return state and state.state == trigger_state
    
    async def _evaluate_template(self, config: Dict[str, Any]) -> bool:
        """Evaluate Jinja2 template trigger."""
        template_str = config.get("template")
        
        if not template_str:
            return False
        
        try:
            tpl = Template(template_str, self.hass)
            rendered = await tpl.async_render_to_info()
            result = rendered.result()
            return result in (True, "True", "true", 1, "1")
        except Exception as e:
            _LOGGER.error(f"Template evaluation error: {e}")
            return False
    
    def _evaluate_logical(self, config: Dict[str, Any]) -> bool:
        """Evaluate logical AND/OR conditions."""
        conditions = config.get("logical_conditions", [])
        operator = config.get("logical_operator", "and")
        
        if not conditions:
            return False
        
        results = []
        for cond in conditions:
            if not isinstance(cond, dict) or "entity_id" not in cond or "state" not in cond:
                _LOGGER.warning(f"Invalid logical condition format: {cond}")
                results.append(False)
                continue
            
            state = self.hass.states.get(cond["entity_id"])
            results.append(state and state.state == cond["state"])
        
        if operator == "or":
            return any(results) if results else False
        else:  # Default to AND
            return all(results) if results else False
    
    def _evaluate_combined(self, config: Dict[str, Any]) -> bool:
        """Evaluate combined trigger with comparators."""
        conditions = config.get("combined_conditions", [])
        operator = config.get("combined_operator", "and")
        
        if not conditions:
            return False
        
        results = []
        for cond in conditions:
            if not isinstance(cond, dict) or "entity_id" not in cond or "value" not in cond:
                _LOGGER.warning(f"Invalid combined condition format: {cond}")
                results.append(False)
                continue
            
            state = self.hass.states.get(cond["entity_id"])
            if not state:
                results.append(False)
                continue
            
            comparator = cond.get("comparator", COMP_EQ)
            results.append(self._compare_values(state.state, comparator, cond["value"]))
        
        if operator == "or":
            return any(results) if results else False
        else:  # Default to AND
            return all(results) if results else False
    
    def _compare_values(self, entity_state: str, comparator: str, expected_value: str) -> bool:
        """Compare entity state using provided comparator."""
        # Attempt numeric comparison first
        def _to_number(value):
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
        
        left_num = _to_number(entity_state)
        right_num = _to_number(expected_value)
        
        # Numeric comparisons
        if comparator in {COMP_LT, COMP_LTE, COMP_GT, COMP_GTE} and left_num is not None and right_num is not None:
            if comparator == COMP_LT:
                return left_num < right_num
            if comparator == COMP_LTE:
                return left_num <= right_num
            if comparator == COMP_GT:
                return left_num > right_num
            if comparator == COMP_GTE:
                return left_num >= right_num
        
        # String comparisons
        if comparator == COMP_EQ:
            return str(entity_state) == str(expected_value)
        if comparator == COMP_NE:
            return str(entity_state) != str(expected_value)
        
        # Default to equality
        return str(entity_state) == str(expected_value)