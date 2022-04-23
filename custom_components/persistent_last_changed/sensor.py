"""The persistent_last_changed sensor class."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (
    CONF_NAME,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    DEVICE_CLASS_TIMESTAMP
)
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.restore_state import RestoreEntity
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .const import (
    CONF_ENTITY,
    CONF_NAME,
    ATTR_LAST_STATE,
    ATTR_LOCAL_FORMAT
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor(s) for Persistent Last Changed platform."""

    entity = config_entry.data.get(CONF_ENTITY)
    name = config_entry.data.get(CONF_NAME)

    unique_id = "sensor.{}".format(slugify(name))

    async_add_entities([
        PersistentLastChangedSensor(
            unique_id,
            name,
            entity
        )
    ])


class PersistentLastChangedSensor(SensorEntity, RestoreEntity):
    """Representation of a Persistent Last Changed Sensor."""

    def __init__(
        self,
        unique_id: str,
        name: str,
        entity: str,
    ) -> None:
        """Initialize a PersistentLastChangedSensor entity."""
        super().__init__()
        self._source_entity = entity
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._state = None
        self._last_state = None

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        await super().async_added_to_hass()

        @callback
        def async_state_changed_listener(event: Event) -> None:
            """Handle child updates."""
            old_state = event.data.get("old_state")
            new_state = event.data.get("new_state")
            old_state = old_state.state if old_state.state else None
            new_state = new_state.state if new_state.state else None

            _LOGGER.debug("Entity {} was changed: old state={}, new state={}".format(event.data.get("entity_id"), old_state, new_state))

            ts = dt_util.now()

            if (
                not new_state or
                new_state in [STATE_UNAVAILABLE, STATE_UNKNOWN] or
                self._last_state == new_state
            ):
                return

            self._state = ts
            self._last_state = new_state

            _LOGGER.debug("Entity {} was updated to {}".format(self.unique_id, ts))
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, self._source_entity, async_state_changed_listener
            )
        )

        prev_state = await self.async_get_last_state()
        if prev_state is not None:
            self._state = dt_util.parse_datetime(prev_state.state)
            self._last_state = prev_state.attributes.get(ATTR_LAST_STATE)

    @property
    def device_class(self) -> str:
        """Return the sensor class of the sensor."""
        return DEVICE_CLASS_TIMESTAMP

    @property
    def native_value(self) -> str:
        """Return the state of the device."""
        if not self._state:
            return dt_util.parse_datetime("2000-01-01 00:00:00").replace(tzinfo=dt_util.UTC)
        return self._state

    @property
    def local_format(self) -> str:
        """Return the state in local format."""
        if not self._state:
            return None
        return dt_util.as_local(self._state)

    @property
    def extra_state_attributes(self):
        """Return the data of the entity."""
        return {
            CONF_ENTITY: self._source_entity,
            ATTR_LAST_STATE: self._last_state,
            ATTR_LOCAL_FORMAT: self.local_format
        }
