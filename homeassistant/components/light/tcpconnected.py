"""
Support for TCP Connected light bulbs.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.tcpconnected/
"""

import logging

import voluptuous as vol

# Import the device class from the component that you want to support
from homeassistant.components.light import ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS, Light, PLATFORM_SCHEMA
from homeassistant.const import CONF_HOST, CONF_ACCESS_TOKEN
import homeassistant.helpers.config_validation as cv

# Home Assistant depends on 3rd party packages for API specific code.
REQUIREMENTS = ['tcpconnected']

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_ACCESS_TOKEN): cv.string,
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the TCP Lighting platform."""
    import sys
    import tcpconnected

    # Assign configuration variables. The configuration check takes care they are
    # present. 
    host = config.get(CONF_HOST)
    access_token = config.get(CONF_ACCESS_TOKEN)

    session = tcpconnected.Session(host, access_token)

    devices = []
    for room in session.getRooms():
        for device in room.getDevices():
            devices.append(TCPConnectedLight(session, device))
            
    add_devices(devices)

def to_tcp_connected_level(level):
    """Convert the given HASS light level (0-255) to TCP Connected (0-100)."""
    return int((level * 100) / 255)


def to_hass_level(level):
    """Convert the given TCP Connected (0-100) light level to HASS (0-255)."""
    return int((level * 255) / 100)

class TCPConnectedLight(Light):
    """Representation of a TCP Connected Light."""

    def __init__(self, session, light):
        """Initialize a TCP Connected light."""
        self._session = session
        self._light = light

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_BRIGHTNESS

    @property
    def name(self):
        """Return the display name of this light."""
        return self._light.getName()

    @property
    def brightness(self):
        """Brightness of the light (an integer in the range 1-255).

        This method is optional. Removing it indicates to Home Assistant
        that brightness is not supported for this light.
        """
        return to_hass_level(self._light.getBrightness())

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._light.isOn()

    def turn_on(self, **kwargs):
        """Instruct the light to turn on.

        You can skip the brightness part if your light does not support
        brightness control.
        """
        hass_brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        tcp_brightness = to_tcp_connected_level(hass_brightness)

        self._session.getGateway().turnOnDevice(self._light)
        self._session.getGateway().setDeviceLevel(self._light, tcp_brightness)

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        self._session.getGateway().turnOffDevice(self._light)

    def update(self):
        """Fetch new state data for this light.
        This is the only method that should fetch new data for Home Assistant.
        """

        self._session.updateState()
