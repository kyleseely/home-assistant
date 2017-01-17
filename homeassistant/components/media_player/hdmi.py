"""
Support for hdmi.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/hdmi_cec/
"""
import logging

import voluptuous as vol

from homeassistant.components.media_player import (
    SUPPORT_TURN_ON, SUPPORT_TURN_OFF, SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_STEP,
    SUPPORT_VOLUME_SET, SUPPORT_SELECT_SOURCE, MediaPlayerDevice,
    PLATFORM_SCHEMA)
from homeassistant.const import (CONF_NAME, STATE_OFF, STATE_ON, EVENT_HOMEASSISTANT_START)
import homeassistant.helpers.config_validation as cv

DEFAULT_NAME = 'TV'

_LOGGER = logging.getLogger(__name__)

SUPPORT_HDMI = SUPPORT_VOLUME_STEP | SUPPORT_VOLUME_MUTE | SUPPORT_VOLUME_SET | \
               SUPPORT_TURN_ON | SUPPORT_TURN_OFF | SUPPORT_SELECT_SOURCE

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})

# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    try:
        import cec
    except ImportError:
        _LOGGER.error("libcec must be installed")
        return False

    # Configure libcec.
    cfg = cec.libcec_configuration()
    cfg.strDeviceName = 'HASS'
    cfg.bActivateSource = 0
    cfg.bMonitorOnly = 1
    cfg.clientVersion = cec.LIBCEC_VERSION_CURRENT

    # Setup CEC adapter.
    _mycec = cec.ICECAdapter.Create(cfg)
    add_devices([HDMIDevice(_mycec, config.get(CONF_NAME))])

    def _start_cec(event):
        """Open CEC adapter."""
        adapters = _mycec.DetectAdapters()
        if len(adapters) == 0:
            _LOGGER.error("No CEC adapter found")
            return

        if _mycec.Open(adapters[0].strComName):
            _LOGGER.debug('Connection opened!')
        else:
            _LOGGER.error("Failed to open adapter")

    hass.bus.listen_once(EVENT_HOMEASSISTANT_START, _start_cec)


class HDMIDevice(MediaPlayerDevice):
    """Representation of an HDMI connected device."""

    def __init__(self, cec, name):
        """Initialize the HDMI connection."""
        _LOGGER.debug('init hdmi device')
        self._cec = cec
        self._name = name
        self._state = STATE_OFF
        self._source = None
        self._volume = None
        self._muted = False

    def update(self):
        _LOGGER.debug('update')
        """Get Power Status of the TV"""
        _LOGGER.debug("GetDevicePowerStatus: " + str(self._cec.GetDevicePowerStatus(0)))
        power_status = self._cec.GetDevicePowerStatus(0)
        if power_status == 0 or power_status == 2:
            _LOGGER.debug('on')
            self._state = STATE_ON
        else:
            _LOGGER.debug('off')
            self._state = STATE_OFF

        self._source = self._cec.GetActiveSource()
        _LOGGER.debug('source' + str(self._source))

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def source(self):
        return self._source

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        if self._volume is not None:
            return self._volume / 100
        else:
            return None

    @property
    def is_volume_muted(self):
        return self._muted

    @property
    def supported_media_commands(self):
        """Flag of media commands that are supported."""
        return SUPPORT_HDMI

    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        pass

    def turn_on(self):
        self._cec.PowerOnDevices()
        self._state = STATE_ON

    def turn_off(self):
        self._cec.StandbyDevices()
        self._state = STATE_OFF

    def volume_up(self):
        self._cec.VolumeUp()

    def volume_down(self):
        self._cec.VolumeDown()

    def mute_volume(self, mute):
        pass

    def select_source(self, source):
        pass