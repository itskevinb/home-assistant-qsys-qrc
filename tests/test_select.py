"""Tests for the select platform's option -> Choices index mapping."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from homeassistant.exceptions import HomeAssistantError

from custom_components.qsys_qrc.select import QRCSelectEntity


def _entity(static_options=None, component=None):
    ent = QRCSelectEntity(
        MagicMock(), "core", MagicMock(), "uid", "name", component, "ctl",
        static_options or [],
    )
    ent.update_control = AsyncMock()
    return ent


@pytest.mark.asyncio
async def test_static_options_in_other_order_use_core_index():
    ent = _entity(static_options=["C", "A"])
    await ent.on_control_changed(None, {"Choices": ["A", "B", "C"], "String": "A"})
    await ent.async_select_option("C")
    ent.update_control.assert_awaited_once_with({"Value": 2})


@pytest.mark.asyncio
async def test_appended_live_value_is_refused():
    ent = _entity()
    await ent.on_control_changed(None, {"Choices": ["A", "B"], "String": "Z"})
    assert ent.options == ["A", "B", "Z"]
    with pytest.raises(HomeAssistantError):
        await ent.async_select_option("Z")
    ent.update_control.assert_not_awaited()


@pytest.mark.asyncio
async def test_auto_options_map_to_core_index():
    ent = _entity()
    await ent.on_control_changed(None, {"Choices": ["A", "B"], "String": "A"})
    await ent.async_select_option("B")
    ent.update_control.assert_awaited_once_with({"Value": 1})


@pytest.mark.asyncio
async def test_static_fallback_before_choices_seen():
    ent = _entity(static_options=["X", "Y"])
    await ent.async_select_option("Y")
    ent.update_control.assert_awaited_once_with({"Value": 1})
    with pytest.raises(HomeAssistantError):
        await ent.async_select_option("nope")
