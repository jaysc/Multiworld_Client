"""
Handles requests to dolphin.
"""
import functools
from asyncio import Task
from typing import Dict

import Dolphin.windWakerInterface as WWI
from Model.coopDto import CoopDto
from Model.multiworldDto import MultiworldDto
from base_logger import logging
from util.abstractGameHandler import AbstractGameHandler
from util.playerInventory import PlayerInventory

logger = logging.getLogger(__name__)


class DolphinGameHandler(AbstractGameHandler):
    def __init__(self, world_id: int, inventory: PlayerInventory, gamemode: str, player_name: str):
        self._world_id = world_id
        self._inventory = inventory
        if gamemode == "Multiworld":
            logger.debug("Set to Multiworld")
            self.take_item = functools.partial(multiworld_take_item, player_world_id=world_id)
            self.give_item = functools.partial(multiworld_give_item, player_world_id=world_id)
            self.dto_factory = functools.partial(multiworld_wrapper, world_id)
        else:
            logger.debug("Set to Coop")
            self.take_item = coop_take_item
            self.give_item = coop_give_item
            self.dto_factory = functools.partial(coop_item_wrapper, player_name)

    async def connect(self):
        WWI.hook()

    async def is_connected(self) -> bool:
        return WWI.is_hooked()

    async def pass_item(self, item_id: int) -> bool:
        try:
            if WWI.is_title_screen():
                return False
            elif not self._inventory.item_maxed(item_id):
                self._inventory.give_item(item_id)
                WWI.give_item_by_value(item_id)
            return True
        except RuntimeError as exc:
            logger.error(exc)
            del exc
            return False

    async def toggle_event(self, event_type: str, event_index: int, enable: bool) -> None:
        pass

    async def get_items(self) -> Dict[int, int]:
        pass

    async def get_queued_items(self) -> MultiworldDto | CoopDto | None:
        target_world, item_id = WWI.read_chest_items()
        if target_world == 0 and item_id == 0:
            return None
        # If the user shouldn't have the item (Multiworld), remove the item from the player.
        elif self.take_item(item_id, target_world, self._inventory):
            logger.debug(f"Removing {item_id} targeting World ID {target_world}")
            WWI.remove_item_by_value(item_id)
        # If the player should have this item, then we want to track it in the Inventory
        elif self.give_item(item_id, target_world, self._inventory):
            logger.debug(f"Giving {item_id} to {target_world}'s Inventory")
            self._inventory.give_item(item_id)
        return self.dto_factory(item_id, target_world)

    async def clear_queued_items(self):
        WWI.clear_chest_items()

    async def verification_loop(self) -> Task:
        pass

def coop_item_wrapper(player_name, item_id, *args) -> CoopDto:
    return CoopDto(sourcePlayerName=player_name, itemId=item_id)

def multiworld_wrapper(source_world, item_id, target_world) -> MultiworldDto:
    return MultiworldDto(sourcePlayerWorldId=source_world, targetPlayerWorldId=target_world, itemId=item_id)

def coop_give_item(item_id: int, target_world: int, player_inventory: PlayerInventory) -> bool:
    return player_inventory.item_maxed(item_id)

def coop_take_item(*args) -> bool:
    return False

def multiworld_give_item(item_id: int, target_world:int, player_inventory: PlayerInventory, player_world_id:int) -> bool:
    return target_world == player_world_id and not player_inventory.item_maxed(item_id)

def multiworld_take_item(item_id: int, target_world:int, player_inventory: PlayerInventory, player_world_id:int) -> bool:
    return target_world != player_world_id and not player_inventory.item_maxed(item_id)
