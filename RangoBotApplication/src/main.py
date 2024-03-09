import os
import sys
import logging
import asyncio
from collections import defaultdict
from decimal import Decimal
from os import environ

import aiohttp_cors
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
import config
from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from rango_client import RangoClient
from aiohttp import web

from rango_response_entities import BestRouteResponse
from utils import amount_to_human_readable, format_output_amount

logger = logging.getLogger(__file__)
dp = Dispatcher()
router = Router()
dp.include_router(router)
rango_client = RangoClient()
bot = Bot(config.TOKEN, parse_mode=ParseMode.MARKDOWN)
users_wallets_dict = defaultdict(set)
users_active_wallet_dict = defaultdict(set)
message_id_map = {}
request_latest_step = defaultdict(int)
request_latest_route = defaultdict(str)

WEB_SERVER_HOST, WEB_SERVER_PORT = environ.get("HOST", "127.0.0.1"), environ.get("PORT", "8070")


@dp.message(CommandStart())
async def command_start_handler(message: Message):
    user_id = message.chat.id
    try:
        request_id, tx_id = message.text.split(' ')[1].split("|")
    except IndexError:
        print('No input param has been identified, proceed with welcome message...')
        msg = "Hey there! \n" \
              "In Rango bot you can easily swap any token to any other token in just 2 steps! " \
              "Please note that only EVM chains are currently supported, other chains will be added soon...\n" \
              "First, connect your wallets with the following format: \n\n" \
              "/wallets BSC.walletAddress\n" \
              "ETH.walletAddress\n" \
              "and other EVM chains"
        return await message.answer(text=msg)


@dp.message(Command('wallets'))
async def wallets(message: Message):
    user_id = message.chat.id
    text = ''.join(message.text.split(' ')[1:])
    if text:
        detected_wallets = text.split('\n')
        if detected_wallets:
            for wallet in detected_wallets:
                users_wallets_dict[user_id].add(wallet)
    else:
        if not users_wallets_dict[user_id]:
            msg = "💳 You don't have any wallets. Add your first wallet like this: /wallets BSC.0x123..."
            return await message.answer(text=msg)
    wallets_msg = 'Your wallets: \n\n'
    if len(users_wallets_dict[user_id]) > 0 and not users_active_wallet_dict.get(user_id):
        for wallet in users_wallets_dict[user_id]:
            users_active_wallet_dict[user_id].add(wallet)
    for wallet in list(users_wallets_dict.get(user_id)):
        sign = '✅' if wallet in users_active_wallet_dict[user_id] else '💳'
        wallets_msg += f"{sign} {wallet} \n"
    await message.answer(text=wallets_msg)


@dp.message(Command('active'))
async def active_wallets(message: Message):
    print(message)
    user_id = message.chat.id
    text = ''.join(message.text.split(' ')[1:])
    users_active_wallet_dict[user_id].add(text)
    msg = "✅ Your active wallet is: %s" % text
    await message.answer(text=msg)


@dp.message(Command('swap'))
async def swap(message: Message):
    print(message)
    user_id = message.chat.id
    text = ' '.join(message.text.split(' ')[1:])
    try:
        from_blockchain_address, to_blockchain_address, amount = text.split(' ')
    except ValueError:
        return await message.answer(text="Enter your desired swap amount at the end of text => /swap "
                                         "BSC.token_address BSC.token_address 20")
    from_blockchain, from_token_address = from_blockchain_address.split('.')
    to_blockchain, to_token_address = to_blockchain_address.split('.')
    connected_wallets = list(users_wallets_dict[user_id])
    selected_wallets = {}
    for item in users_active_wallet_dict[user_id]:
        blockchain, wallet_address = item.split('.')
        selected_wallets[blockchain] = wallet_address
    best_route_response: BestRouteResponse = await rango_client.route(connected_wallets, selected_wallets,
                                                                      from_blockchain,
                                                                      from_token_address,
                                                                      to_blockchain,
                                                                      to_token_address, float(amount))
    request_id = best_route_response.requestId
    swaps = best_route_response.result.swaps
    swap_path, fee_amount_msg = '', ''
    for swap in swaps:
        from_amount = '%.3f' % Decimal(swap.fromAmount)
        to_amount = '%.3f' % Decimal(swap.toAmount)
        from_blockchain_symbol = f'{from_amount} {swap.from_.blockchain}.{swap.from_.symbol}'
        to_blockchain_symbol = f'{to_amount} {swap.to.blockchain}.{swap.to.symbol}'
        swapper = f'{swap.swapperId} ({swap.swapperType})'
        swap_path += from_blockchain_symbol + " -> " + swapper + " -> " + to_blockchain_symbol
        for fee in swap.fee:
            fee_amount_msg += f'`{fee.name}`: `{format_output_amount(fee.amount)} {fee.asset.blockchain}.{fee.asset.symbol}` \n'

    request_latest_route[user_id] = request_id

    mk_b = InlineKeyboardBuilder()
    mk_b.button(text='Confirm Swap', callback_data=f'confirmSwap|{request_id}')
    msg = "🔹 The best route is: \n\n" \
          "🛣 %s \n \n " \
          "⛽️ %s \n \n " \
          "❓If you're happy with the rate and the fee, confirm the swap" % (swap_path, fee_amount_msg)
    message = await message.answer(text=msg, reply_markup=mk_b.as_markup())
    print(message)
    message_id_map[user_id] = str(message.message_id)


@dp.message(Command('popular'))
async def get_populars(message: Message):
    tokens = await rango_client.popular_tokens()
    tokens_msg, c = '', 1
    for token in tokens:
        if token["address"] is not None and len(token["address"]) > 5 and token['blockchain'] in ['POLYGON', 'BSC',
                                                                                                  'ETH', 'ARBITRUM'] and \
                token['symbol'] in ['USDT', 'USDC', 'DAI']:
            tokens_msg += f'🔹 `{token["blockchain"]}.{token["symbol"]}` -> `{token["address"]}`\n'
            c += 1
        if c > 15:
            break
    return await message.answer(text=tokens_msg)


@dp.message(Command('balance'))
async def balance(message: Message):
    print(message)
    user_id = message.chat.id
    user_wallets = users_wallets_dict[user_id]
    text = ''.join(message.text.split(' ')[1:])
    if text:
        wallet_addresses = [text]
    elif user_wallets:
        wallet_addresses = list(user_wallets)
    else:
        return message.answer(text='Please add your wallets by typing /wallets Blockchain.Address like BSC.0x...')
    wallets = await rango_client.balance(wallet_addresses)
    balance_msg = ''
    for w in wallets:
        balance_msg += f'⛓ Blockchain: {w.get("blockChain")} \n'
        balances = w['balances']
        if balances:
            for balance in balances:
                asset = balance['asset']
                address = asset.get('address', '')
                amount = balance['amount']
                balance_msg += f"\t ▪️ {asset['symbol']} (`{address}`): {amount_to_human_readable(amount['amount'], amount['decimals'], 3)} \n"
        else:
            balance_msg += '\t ▪️ No assets! \n'
    return await message.answer(text=balance_msg)


async def confirm_swap(message: Message, request_id: str):
    print("request_id: " + request_id)
    user_id = message.chat.id
    msg_id = message_id_map[user_id]
    request_latest_step[request_id] = request_latest_step.get(request_id, 0) + 1
    is_success, sign_tx_or_error = await rango_client.create_transaction(user_id, request_id)
    if not is_success:
        res = await message.edit_text(text=f'❌ {sign_tx_or_error}', inline_message_id=msg_id)
        message_id_map[user_id] = str(res.message_id)
        return
    approved_before = await only_check_approval_status_looper(max_retry=2, request_id=request_id)
    if is_success and not approved_before:
        msg = f"Please approve the tx by clicking on the button 👇 \n" \
              f"Waiting for you approval..."
        mk_b = InlineKeyboardBuilder()
        mk_b.button(text='Approve Transaction', url=sign_tx_or_error)
        asyncio.create_task(check_approval_status_looper(message, request_id))
        res = await message.edit_text(text=msg, inline_message_id=msg_id, reply_markup=mk_b.as_markup())
        message_id_map[user_id] = str(res.message_id)
        return
    elif approved_before and is_success:
        msg = f"Please sign the tx by clicking on the button 👇"
        mk_b = InlineKeyboardBuilder()
        mk_b.button(text='Sign Transaction', url=sign_tx_or_error)
        res = await message.edit_text(text=msg, inline_message_id=msg_id, reply_markup=mk_b.as_markup())
        message_id_map[user_id] = str(res.message_id)
        return
    else:
        res = await message.edit_text(text=sign_tx_or_error, inline_message_id=msg_id)
        message_id_map[user_id] = str(res.message_id)


async def sign_tx(message: Message, request_id: str):
    print("Sign request_id: " + request_id)
    print(message)
    user_id = message.chat.id
    msg_id = message_id_map[user_id]
    is_success, sign_tx_url = await rango_client.create_transaction(user_id, request_id)
    if is_success:
        msg = f"Please sign the tx by clicking on the button 👇"
        mk_b = InlineKeyboardBuilder()
        mk_b.button(text='Sign Transaction', url=sign_tx_url)
        res = await message.edit_text(text=msg, inline_message_id=msg_id, reply_markup=mk_b.as_markup())
        message_id_map[user_id] = str(res.message_id)
        return
    else:
        res = await message.edit_text(text=f"An error has occurred!", inline_message_id=msg_id)
        message_id_map[user_id] = str(res.message_id)
        return


async def only_check_approval_status_looper(max_retry: int, request_id: str):
    print(f"Only check approval status looper is called, req: {request_id}")
    is_approved = False
    retry = 0
    while not is_approved:
        is_approved = await rango_client.check_approval(request_id)
        retry += 1
        print(f"retry: {retry}, approve status: {is_approved}")
        if retry >= max_retry:
            return False
        await asyncio.sleep(1)
    print(f"out of loop, approve status: {is_approved}")
    if is_approved:
        print("TX is approved, returning True...")
        return True
    return False


async def check_approval_status_looper(message: Message, request_id: str):
    print(f"Check approval status looper is called, req: {request_id}")
    user_id = message.chat.id
    is_approved = False
    msg_id = message_id_map[user_id]
    retry = 0
    while not is_approved:
        is_approved = await rango_client.check_approval(request_id)
        await asyncio.sleep(1)
        retry += 1
        print(f"retry: {retry}, approve status: {is_approved}")
        if retry > 100:
            return False
    print(f"out of loop, approve status: {is_approved}")
    if is_approved:
        print("TX is approved, calling send sign tx...")
        msg = '✅ Transaction is approved!'
        res = await message.edit_text(text=msg, inline_message_id=msg_id)
        message_id_map[user_id] = str(res.message_id)
        return await sign_tx(message, request_id)
    return True


async def check_tx_sign_status_looper(user_id: int, request_id: str, tx_id: str, step: int):
    print(message_id_map)
    msg_id = message_id_map[user_id]
    print(f'msg_id: {msg_id}, user_id: {user_id}')
    print(f"Check tx sign status looper is called, req: {request_id}, user_id: {user_id}, step: {step}")
    is_tx_signed, tx = False, None
    retry = 0
    while not is_tx_signed:
        tx = await rango_client.check_tx(request_id, tx_id, step)
        is_tx_signed = tx.is_successful()
        await asyncio.sleep(2)
        retry += 1
        print(f"retry: {retry}, approve status: {is_tx_signed}")
        if retry > 100:
            return False
    print(f"out of loop, approve status: {is_tx_signed}")
    if is_tx_signed and tx:
        route = request_latest_route[user_id]
        msg = '✅ Your swap with the following route has been successfully completed! \n' \
              '🔹 route: %s \n' \
              '🔹 Output amount: %s \n' \
              '%s' % (route, tx.get_output_amount(), tx.print_explorer_urls())
        return await bot.edit_message_text(text=msg, chat_id=user_id, message_id=int(msg_id))
    if tx:
        msg = tx.extraMessage
    else:
        msg = 'An error has been occurred, please contact admin!'
    return await bot.edit_message_text(text=msg, chat_id=user_id, inline_message_id=msg_id)


async def main() -> None:
    bot_info = await bot.get_me()
    print(bot_info)
    await bot.delete_webhook(drop_pending_updates=True)  # skip_updates = True
    await dp.start_polling(bot)


async def check_status_handler(request):
    print("in check_status_handler...")
    tx_hash = request.query.get('tx_hash', None)
    request_id = request.query.get('request_id', None)
    tg_user_id = int(request.query.get('tg_user_id', None))
    print(tx_hash)
    print(request_id)
    print(tg_user_id)
    step = request_latest_step[request_id]
    asyncio.create_task(check_tx_sign_status_looper(tg_user_id, request_id, tx_hash, step))
    return web.Response(text="Received!")


@dp.callback_query(lambda call: True)
async def main_callback_handler(call: CallbackQuery):
    await call.answer()
    message = call.message
    data = call.data
    if data == "start":
        await command_start_handler(message)
    elif data == "balance":
        await balance(message)
    elif data == "popular":
        await get_populars(message)
    elif data == "wallets":
        await wallets(message)
    elif data == "swap":
        await swap(message)
    elif data.startswith("confirmSwap"):
        _, request_id = data.split('|')
        await confirm_swap(message, request_id)


async def on_startup(dispatcher: Dispatcher, bot: Bot):
    await bot.set_webhook(f'https://rangobot.cryptoeye.app')


def webhook_main():
    dp.startup.register(on_startup)
    app = web.Application()
    app.router.add_route('GET', '/check_status', check_status_handler)
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    # Register webhook handler on application
    webhook_requests_handler.register(app, path="")

    # Mount dispatcher startup and shutdown hooks to aiohttp application
    setup_application(app, dp, bot=bot)

    # Configure CORS
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    # Apply CORS to all routes
    for route in list(app.router.routes()):
        cors.add(route)

    # Port for incoming request from reverse proxy. Should be any available port
    web.run_app(app, host=WEB_SERVER_HOST, port=int(WEB_SERVER_PORT))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    is_test = os.environ.get('DEVELOPMENT', False)
    if is_test:
        asyncio.run(main())
    else:
        webhook_main()