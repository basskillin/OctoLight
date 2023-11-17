import octoprint.plugin
from octoprint.events import Events
import flask
import subprocess

class OctoLightPlugin(
        octoprint.plugin.AssetPlugin,
        octoprint.plugin.StartupPlugin,
        octoprint.plugin.TemplatePlugin,
        octoprint.plugin.SimpleApiPlugin,
        octoprint.plugin.SettingsPlugin,
        octoprint.plugin.EventHandlerPlugin,
        octoprint.plugin.RestartNeedingPlugin
    ):

    light_state = False

    def get_settings_defaults(self):
        return dict(
            light_pin = 16,
            inverted_output = False
        )

    def get_template_configs(self):
        return [
            dict(type="navbar", custom_bindings=True),
            dict(type="settings", custom_bindings=True)
        ]

    def get_assets(self):
        return dict(
            js=["js/octolight.js"],
            css=["css/octolight.css"],
        )

    def on_after_startup(self):
        self.light_state = False
        self._logger.info("--------------------------------------------")
        self._logger.info("OctoLight started, listening for GET request")
        self._logger.info("Light pin: {}, inverted_input: {}".format(
            self._settings.get(["light_pin"]),
            self._settings.get(["inverted_output"])
        ))
        self._logger.info("--------------------------------------------")

        # Setting the default state of pin
        subprocess.call(["sudo", "lgpio", "set", "{}=0".format(self._settings.get(["light_pin"]))])

        self.light_state = False
        self._plugin_manager.send_plugin_message(self._identifier, dict(isLightOn=self.light_state))

    def light_toggle(self):
        self.light_state = not self.light_state

        if self.light_state ^ self._settings.get(["inverted_output"]):
            subprocess.call(["sudo", "lgpio", "set", "{}=1".format(self._settings.get(["light_pin"]))])
        else:
            subprocess.call(["sudo", "lgpio", "set", "{}=0".format(self._settings.get(["light_pin"]))])

        self._logger.info("Got request. Light state: {}".format(
            self.light_state
        ))

        self._plugin_manager.send_plugin_message(self._identifier, dict(isLightOn=self.light_state))

    def on_api_get(self, request):
        action = request.args.get('action', default="toggle", type=str)

        if action == "toggle":
            self.light_toggle()

            return flask.jsonify(state=self.light_state)

        elif action == "getState":
            return flask.jsonify(state=self.light_state)

        elif action == "turnOn":
            if not self.light_state:
                self.light_toggle()

            return flask.jsonify(state=self.light_state)

        elif action == "turnOff":
            if self.light_state:
                self.light_toggle()

            return flask.jsonify(state=self.light_state)

        else:
            return flask.jsonify(error="action not recognized")

    def on_event(self, event, payload):
        if event == Events.CLIENT_OPENED:
            self._plugin_manager.send_plugin_message(self._identifier, dict(isLightOn=self.light_state))
            return

    def get_update_information(self):
        return dict(
            octolight=dict(
                displayName="OctoLight",
                displayVersion=self._plugin_version,

                type="github_release",
                current=self._plugin_version,

                user="supprt",
                repo="OctoLight",
                pip="https://git.mobileitgeeks.com/support/OctoLight/archive/{target}.zip"
            )
        )

__plugin_pythoncompat__ = ">=2.6<4"
__plugin_implementation__ = OctoLightPlugin()

__plugin_hooks__ = {
    "octoprint.plugin.softwareupdate.check_config":
    __plugin_implementation__.get_update_information
}
