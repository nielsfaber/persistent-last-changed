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
from homeassistant.helpers.event import (async_track_state_change_event, async_track_point_in_time)
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .const import (
    CONF_ENTITY,
    CONF_EXPIRATION_TIME,
    CONF_NAME,
    ATTR_LAST_STATE,
    ATTR_LOCAL_FORMAT,
    ATTR_IS_EXPIRED
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
    expiration_time = config_entry.data.get(CONF_EXPIRATION_TIME)

    unique_id = "sensor.{}".format(slugify(name))

    async_add_entities([
        PersistentLastChangedSensor(
            unique_id,
            name,
            entity,
            expiration_time
        )
    ])


class PersistentLastChangedSensor(SensorEntity, RestoreEntity):
    """Representation of a Persistent Last Changed Sensor."""

    def __init__(
        self,
        unique_id: str,
        name: str,
        entity: str,
        expiration_time: int
    ) -> None:
        """Initialize a PersistentLastChangedSensor entity."""
        super().__init__()
        self._source_entity = entity
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._state = None
        self._last_state = None
        self._expiration_time = expiration_time
        self._is_expired = False
        self._timer = None

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
                new_state == old_state or
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
            self._is_expired = prev_state.attributes.get(ATTR_IS_EXPIRED)

        await self.async_set_timer()

    async def async_set_timer(self) -> None:
        """start timer for next day at 12:00"""
        if self._timer:
            self._timer()
            self._timer = None

        if not self._expiration_time:
            return

        now = dt_util.as_local(dt_util.utcnow())
        ts = dt_util.find_next_time_expression_time(
            now, [0], [0], [12]
        )
        if (ts - now).total_seconds() <= 1:
            now = now + dt_util.dt.timedelta(days=1)
            ts = dt_util.find_next_time_expression_time(
                now, [0], [0], [12]
            )

        _LOGGER.debug("Timer is set for {}".format(ts))
        self._timer = async_track_point_in_time(
            self.hass, self.async_timer_finished, ts
        )

    async def async_timer_finished(self, _time):
        """timer is expired"""

        now = dt_util.now()
        ts = self._state if self._state else now

        days_delta = (now - ts).total_seconds() / (24*3600)
        is_expired = days_delta >= self._expiration_time

        _LOGGER.debug("Expiration state for {} was recalculated: old={}, new={}".format(self.unique_id, self._is_expired, is_expired))

        if self._is_expired != is_expired:
            self._is_expired = is_expired
            self.async_write_ha_state()

        await self.async_set_timer()

    async def async_will_remove_from_hass(self) -> None:
        """entity is to be removed"""
        if self._timer:
            self._timer()

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
            ATTR_LOCAL_FORMAT: self.local_format,
            CONF_EXPIRATION_TIME: self._expiration_time,
            ATTR_IS_EXPIRED: self._is_expired
        }
