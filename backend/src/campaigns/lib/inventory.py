import uuid
from typing import List, Optional
from src.schemas.item_instance import ItemInstance
from src.schemas.item import ItemResponse

class InventoryManager:
    @staticmethod
    def add_item(inventory: List[ItemInstance], item_template: ItemResponse, quantity: int = 1) -> ItemInstance:
        """
        Adds an item to the inventory. 
        If the item is stackable (logic to be defined, assuming all are for now if same ID), 
        it might stack. For now, we create a new instance for unique tracking.
        """
        # TODO: Check for existing stackable items and merge if applicable.
        
        new_instance = ItemInstance(
            id=str(uuid.uuid4()),
            item_id=item_template.id,
            template=item_template,
            quantity=quantity,
            equipped=False,
            attuned=False
        )
        inventory.append(new_instance)
        return new_instance

    @staticmethod
    def remove_item(inventory: List[ItemInstance], instance_id: str, quantity: int = 1) -> bool:
        """
        Removes an item or reduces quantity. Returns True if successful.
        """
        for i, item in enumerate(inventory):
            if item.id == instance_id:
                if item.quantity > quantity:
                    item.quantity -= quantity
                    return True
                elif item.quantity == quantity:
                    inventory.pop(i)
                    return True
                else:
                    return False # Not enough quantity
        return False

    @staticmethod
    def equip_item(inventory: List[ItemInstance], instance_id: str) -> bool:
        """
        Equips an item. Handles basic logic (e.g. unequip other armor if equipping armor).
        """
        target_item = next((i for i in inventory if i.id == instance_id), None)
        if not target_item:
            return False
            
        # Basic logic: If it's armor, unequip other armor
        # This requires the template to be present
        if target_item.template and target_item.template.type == "Armor":
             for item in inventory:
                 if item.equipped and item.template and item.template.type == "Armor" and item.id != instance_id:
                     item.equipped = False
        
        target_item.equipped = True
        return True

    @staticmethod
    def unequip_item(inventory: List[ItemInstance], instance_id: str) -> bool:
        target_item = next((i for i in inventory if i.id == instance_id), None)
        if not target_item:
            return False
        
        target_item.equipped = False
        return True
