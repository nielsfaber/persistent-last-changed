"""Store constants."""

NAME = "Persistent Last Changed"
DOMAIN ="persistent_last_changed"

CONF_ENTITY = "entity"
CONF_NAME = "name"
ATTR_LAST_STATE = "last_state"
ATTR_LOCAL_FORMAT = "local_format"

SUPPORTED_DOMAINS = [
  "binary_sensor",
  "climate",
  "cover",
  "fan",
  "light",
  "sensor",
  "switch"
]