from homeassistant.components.button import ButtonEntity
from .supbowl import LifeSmartSupBowlAPI
DOMAIN = "lifesmart_1"


async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    remotes = data["remotes"]
    api = data["supbowl_api"]

    entities = []
    for ai, info in remotes.items():
        remote_name = info["name"]
        category = info["category"]
        brand = info["brand"]
        detail = await hass.async_add_executor_job(api.get_remote_detail, ai)
        for btn in detail.get("keys", []):
            entities.append(SupBowlIRButton(
                ai, remote_name, category, brand, btn, api
            ))
    async_add_entities(entities)

class SupBowlIRButton(ButtonEntity):
    def __init__(self, ai, remote_name, category, brand, btn, api):
        self._attr_name = f"{remote_name}-{btn}"
        self._attr_unique_id = f"{ai}_{btn}"
        self._ai = ai
        self._category = category
        self._brand = brand
        self._btn = btn
        self._api = api

    async def async_press(self):
        await self.hass.async_add_executor_job(
            self._api.send_keys,
            self._ai, self._category, self._brand, self._btn
        )
