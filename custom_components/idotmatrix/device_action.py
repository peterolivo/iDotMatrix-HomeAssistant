"""Device actions for iDotMatrix."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_TYPE
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import config_validation as cv, device_registry as dr

from .const import DOMAIN
from .coordinator import IDotMatrixCoordinator

ACTION_DISPLAY_GIF = "display_gif"
ACTION_STOP_GIF_ROTATION = "stop_gif_rotation"
ACTION_TYPES = {ACTION_DISPLAY_GIF, ACTION_STOP_GIF_ROTATION}

CONF_PATH = "path"
CONF_ROTATION_INTERVAL = "rotation_interval"

_DISPLAY_GIF_FIELDS = {
    vol.Required(CONF_PATH): cv.string,
    vol.Optional(CONF_ROTATION_INTERVAL, default=5): vol.All(
        vol.Coerce(int), vol.Range(min=1, max=255)
    ),
}

ACTION_SCHEMA = vol.Any(
    cv.DEVICE_ACTION_BASE_SCHEMA.extend(
        {vol.Required(CONF_TYPE): ACTION_DISPLAY_GIF, **_DISPLAY_GIF_FIELDS}
    ),
    cv.DEVICE_ACTION_BASE_SCHEMA.extend(
        {vol.Required(CONF_TYPE): ACTION_STOP_GIF_ROTATION}
    ),
)


async def async_get_actions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """Return the list of device actions for an iDotMatrix device."""
    base = {CONF_DEVICE_ID: device_id, CONF_DOMAIN: DOMAIN}
    return [
        {**base, CONF_TYPE: ACTION_DISPLAY_GIF},
        {**base, CONF_TYPE: ACTION_STOP_GIF_ROTATION},
    ]


async def async_call_action_from_config(
    hass: HomeAssistant,
    config: dict[str, Any],
    variables: dict[str, Any],
    context: Context | None,
) -> None:
    """Execute a device action."""
    coordinator = _coordinator_for_device(hass, config[CONF_DEVICE_ID])
    action_type = config[CONF_TYPE]
    if action_type == ACTION_DISPLAY_GIF:
        await coordinator.async_display_gif(
            path=config[CONF_PATH],
            rotation_interval=config.get(CONF_ROTATION_INTERVAL, 5),
        )
    elif action_type == ACTION_STOP_GIF_ROTATION:
        await coordinator.async_stop_gif_rotation()


async def async_get_action_capabilities(
    hass: HomeAssistant, config: dict[str, Any]
) -> dict[str, vol.Schema]:
    """Return form fields for the action editor in the automation UI."""
    if config[CONF_TYPE] == ACTION_DISPLAY_GIF:
        return {"extra_fields": vol.Schema(_DISPLAY_GIF_FIELDS)}
    return {"extra_fields": vol.Schema({})}


def _coordinator_for_device(
    hass: HomeAssistant, device_id: str
) -> IDotMatrixCoordinator:
    """Resolve a device_id to its iDotMatrix coordinator."""
    device = dr.async_get(hass).async_get(device_id)
    if device is None:
        raise ValueError(f"Unknown device {device_id}")
    domain_data = hass.data.get(DOMAIN, {})
    for entry_id in device.config_entries:
        coordinator = domain_data.get(entry_id)
        if isinstance(coordinator, IDotMatrixCoordinator):
            return coordinator
    raise ValueError(f"No iDotMatrix coordinator for device {device_id}")
