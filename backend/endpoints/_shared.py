from typing import Literal, TypedDict


class Message(TypedDict):
    role: Literal["system", "assistant", "user"]
    content: str


MESSAGES: dict[str, list[Message]] = {}

SYSTEM_PROMPT = 'Strictly answer in English. You are a chat bot whose job is to complete information from user of database entries for food menu, you should expect from user to give you following values for every entry: Item Name, Item Type (One of Dish, Sandwich, Drink), Item Unit Price, Item Preparation Time. When user begins asking you to create new entry take whatever user passes and request the missing until all are complete, then confirm with user all the info again, and when user confirms reply with "Item is being created" only.'
#If user asks for menu reply with "Fetching menu items...".'

JSON_PROMPT = 'Format the item details as json with following keys "name", "type" in lower case, "unit_price" with value in cents, and "preparation_time" with value in minutes. add three back ticks around the json block'


class Item(TypedDict):
    name: str
    type: Literal["dish", "sandwich", "drink"]
    unit_price: int
    preparation_time: int


MENU: dict[str, list[Item]] = {
    "971556556400": [
        {
            "name": "Spaghetti",
            "type": "dish",
            "unit_price": 3400,
            "preparation_time": 25,
        },
        {
            "name": "golden burger",
            "type": "sandwich",
            "unit_price": 1200,
            "preparation_time": 4,
        },
        {
            "name": "Mashawi Plate",
            "type": "dish",
            "unit_price": 7500,
            "preparation_time": 30,
        },
    ]
}
