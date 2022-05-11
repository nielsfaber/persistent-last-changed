"""Store constants."""

NAME = "Persistent Last Changed"
DOMAIN ="persistent_last_changed"

CONF_ENTITY = "entity"
CONF_NAME = "name"
CONF_EXPIRATION_TIME = "expiration_time"

ATTR_LAST_STATE = "last_state"
ATTR_LOCAL_FORMAT = "local_format"
ATTR_IS_EXPIRED = "is_expired"

SUPPORTED_DOMAINS = [
  "binary_sensor",
  "climate",
  "cover",
  "fan",
  "light",
  "sensor",
  "switch"
]