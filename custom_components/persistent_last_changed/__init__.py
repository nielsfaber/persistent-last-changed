"""The persistent_last_changed component."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from . import const

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Track states and offer events for sensors."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Persistant Last Changed integration from a config entry."""

    hass.data.setdefault(const.DOMAIN, {})
    hass.data[const.DOMAIN][entry.entry_id] = {}

    # Set up all platforms for this device/entry.
    hass.config_entries.async_setup_platforms(entry, [Platform.SENSOR])

    # Reload entry when its updated.
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when it changed."""

    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry):
    """Unload Zoned Heating config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, [Platform.SENSOR])

    if unload_ok:
        hass.data[const.DOMAIN].pop(entry.entry_id)

    return unload_ok
