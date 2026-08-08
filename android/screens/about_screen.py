"""About screen: app identity, Android version, privacy summary, and the
Juniper-relationship statement (adapted from the desktop app/website
wording, not reworded into new claims)."""

from __future__ import annotations

from kivy.properties import StringProperty
from kivy.uix.screenmanager import Screen

from android_constants import ANDROID_APP_VERSION, JUNIPER_RELATIONSHIP_TEXT, PRIVACY_SUMMARY
from cinqic_calculator import constants


class AboutScreen(Screen):
    app_name = StringProperty(constants.APP_NAME)
    version_text = StringProperty(f"Version {ANDROID_APP_VERSION} (Android)")
    privacy_text = StringProperty(PRIVACY_SUMMARY)
    juniper_text = StringProperty(JUNIPER_RELATIONSHIP_TEXT)
