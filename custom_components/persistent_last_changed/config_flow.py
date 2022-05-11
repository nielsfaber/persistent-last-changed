"""Config flow for the Persistant Last Changed component."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from . import const

_LOGGER = logging.getLogger(__name__)


def get_entities(hass):
    entities = [
        entity
        for entity in hass.states.async_entity_ids()
        if entity.split(".").pop(0) in const.SUPPORTED_DOMAINS
    ]
    return entities


class ConfigFlow(config_entries.ConfigFlow, domain=const.DOMAIN):
    """Config flow for Persistent Last Changed."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    def __init__(self):
        self._entity = None
        self._name = None
        self._expiration_time = None

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""

        if user_input is not None:
            self._entity = user_input[const.CONF_ENTITY]
            return await self.async_step_name()

        all_entities = get_entities(self.hass)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        const.CONF_ENTITY
                    ): vol.In(sorted(all_entities)),
                }
            ),
        )

    async def async_step_name(self, user_input=None):
        """Handle a flow initialized by the user."""

        friendly_name = self.hass.states.get(self._entity).attributes["friendly_name"]
        default_name = "{} Last Changed".format(friendly_name)

        if user_input is not None:
            self._name = user_input[const.CONF_NAME]

            return await self.async_step_expiration()

        return self.async_show_form(
            step_id="name",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        const.CONF_NAME,
                        default=default_name
                    ): str,
                }
            ),
        )

    async def async_step_expiration(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self._expiration_time = user_input[const.CONF_EXPIRATION_TIME]

            return self.async_create_entry(title=self._name, data={
                const.CONF_ENTITY: self._entity,
                const.CONF_NAME: self._name,
                const.CONF_EXPIRATION_TIME: self._expiration_time
            })

        return self.async_show_form(
            step_id="expiration",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        const.CONF_EXPIRATION_TIME,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=0, max=100),
                    )
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow for Zoned Heating."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

        self._entity = config_entry.data.get(const.CONF_ENTITY)
        self._name = None
        self._expiration_time = config_entry.data.get(const.CONF_EXPIRATION_TIME)

    async def async_step_init(self, user_input=None):
        """Handle options flow."""

        if user_input is not None:
            self._entity = user_input[const.CONF_ENTITY]
            return await self.async_step_name()

        all_entities = get_entities(self.hass)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        const.CONF_ENTITY,
                        default=self._entity
                    ): vol.In(sorted(all_entities)),
                }
            ),
        )

    async def async_step_name(self, user_input=None):
        """Handle a flow initialized by the user."""

        friendly_name = self.hass.states.get(self._entity).attributes["friendly_name"]
        default_name = "{} Last Changed".format(friendly_name)

        if user_input is not None:
            self._name = user_input[const.CONF_NAME]
            return await self.async_step_expiration()

        return self.async_show_form(
            step_id="name",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        const.CONF_NAME,
                        default=default_name
                    ): str,
                }
            ),
        )

    async def async_step_expiration(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self._expiration_time = user_input[const.CONF_EXPIRATION_TIME]

            self.hass.config_entries.async_update_entry(self.config_entry, title=self._name, data={
                const.CONF_ENTITY: self._entity,
                const.CONF_NAME: self._name,
                const.CONF_EXPIRATION_TIME: self._expiration_time
            })

            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="expiration",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        const.CONF_EXPIRATION_TIME,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=0, max=100),
                    )
                }
            ),
        )
