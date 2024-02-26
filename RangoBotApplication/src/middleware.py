from aiogram import BaseMiddleware
from aiogram.types import Message


class txHashReceiverMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message: Message, data: dict):
        print("on_pre_process_message is called...")
        print(data)
        print(message)


