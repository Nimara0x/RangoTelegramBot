import json
from decimal import Decimal
from typing import Optional
import asyncio, base64
from aiogram.client.session import aiohttp

from rango_entities import TransactionObject
from utils import Singleton
import config


class RangoClient(Singleton):

    def __init__(self):
        super().__init__()
        self.api_key = config.RANGO_API_KEY
        self.base_url = config.RANGO_BASE_URL
        self.meta = None
        self._popular_tokens = None
        asyncio.run(self.post_init())

    async def post_init(self):
        url = f"meta"
        response: dict = await self.__request(url, "GET")
        self.meta = response
        params = {'excludeNonPopulars': True}
        popular_response: dict = await self.__request(url, "GET", extra_params=params)
        self._popular_tokens = popular_response
        print('Meta has been initialized...')

    def __get_token_data(self, blockchain: str, token_address: Optional[str]):
        for token in self.meta['tokens']:
            if token['blockchain'] == blockchain.upper() and token['address'] == token_address.lower():
                return token

    async def popular_tokens(self):
        return self._popular_tokens['popularTokens']

    async def __request(self, url: str, method: str, data=None, extra_params=None, list_params=None) -> dict:
        if extra_params is None:
            extra_params = {}
        if data is None:
            data = {}

        params = {
            'apiKey': self.api_key
        }
        params.update(extra_params)
        encoded_params = '&'.join([f"{key}={value}" for key, value in params.items()])
        if list_params:
            encoded_params += '&'
            encoded_params += '&'.join([param for param in list_params])
        base_url = self.base_url + url
        req_url = base_url + '?' + encoded_params
        headers = {"accept": "*/*", "content-type": "application/json"}
        print(f"final url: {req_url}")
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.request(
                    method,
                    headers=headers,
                    url=req_url,
                    json=data
            ) as resp:
                response = await resp.json()
                return response

    async def balance(self, wallet_addresses: list[str]):
        url = f"wallets/details"
        list_params = []
        for bwa in wallet_addresses:
            list_params.append(f'address={bwa}')
        response: dict = await self.__request(url, "GET", list_params=list_params)
        print(response)
        wallets = response.get('wallets')
        return wallets

    async def route(self, _connected_wallets: list, selected_wallets: dict, from_blockchain: str,
                    from_token_address: str,
                    to_blockchain: str, to_token_address: str, amount: float):
        url = f"routing/best"
        from_token = self.__get_token_data(from_blockchain, from_token_address)
        to_token = self.__get_token_data(to_blockchain, to_token_address)
        connected_wallets = []

        for item in _connected_wallets:
            blockchain, address = item.split('.')
            connected_wallets.append(
                {'blockchain': blockchain, 'addresses': [address]}
            )
        payload = {
            "from": {
                "blockchain": from_blockchain.upper(),
                "symbol": from_token['symbol'],
                "address": from_token_address
            },
            "to": {
                "blockchain": to_blockchain.upper(),
                "symbol": to_token['symbol'],
                "address": to_token_address
            },
            "checkPrerequisites": False,
            "connectedWallets": connected_wallets,
            "selectedWallets": selected_wallets,
            "amount": amount,
            "maxLength": 1
        }
        response: dict = await self.__request(url, "POST", data=payload)
        best_route = response
        request_id = best_route['requestId']
        swaps = best_route['result']['swaps']
        swap_path = ''
        for swap in swaps:
            from_amount = '%.3f' % Decimal(swap["fromAmount"])
            to_amount = '%.3f' % Decimal(swap["toAmount"])
            from_blockchain_symbol = f'{from_amount} {swap["from"]["blockchain"]}.{swap["from"]["symbol"]}'
            to_blockchain_symbol = f'{to_amount} {swap["to"]["blockchain"]}.{swap["to"]["symbol"]}'
            swapper = f'{swap["swapperId"]} ({swap["swapperType"]})'
            swap_path += from_blockchain_symbol + " -> " + swapper + " -> " + to_blockchain_symbol
        print(swap_path)
        return request_id, swap_path

    async def create_transaction(self, tg_user_id: int, request_id: str, step: int = 1, slippage: int = 2):
        url = f"tx/create"
        payload = {
            "userSettings": {
                "slippage": slippage
            },
            "validations": {
                "balance": True,
                "fee": True,
                "approve": True
            },
            "requestId": request_id,
            "step": step,
        }
        response: dict = await self.__request(url, "POST", data=payload)
        print(response)
        if not response['ok']:
            return False, response.get("error")
        resp_tx = response['transaction']
        resp_tx['reqId'] = request_id
        resp_tx['tgUserId'] = tg_user_id
        tx: json = json.dumps(resp_tx)
        encoded_string = base64.b64encode(tx.encode()).decode()
        # wallet_url = f'https://metamask.app.link/dapp/test-dapp-pearl.vercel.app/?param={encoded_string}'
        wallet_url = f'https://test-dapp-pearl.vercel.app/?param={encoded_string}'
        return True, wallet_url

    async def check_approval(self, request_id: str) -> bool:
        url = f"tx/{request_id}/check-approval"
        response: dict = await self.__request(url, "GET")
        print(response)
        return response["isApproved"]

    async def check_tx(self, request_id: str, tx_id: str, step: int) -> TransactionObject:
        url = f"tx/check-status"
        payload = {
            "requestId": request_id,
            "txId": tx_id,
            "step": step,
        }
        response_json = await self.__request(url, "POST", data=payload)
        transaction_object: TransactionObject = TransactionObject.from_dict(response_json)
        return transaction_object

