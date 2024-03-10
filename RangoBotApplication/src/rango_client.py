from typing import Optional, Any
import asyncio
from aiogram.client.session import aiohttp
from rango_response_entities import TransactionObject, MetaResponse, BalanceResponse
from rango_request_entities import BestRouteResponse
from utils import Singleton
import config


class RangoClient(Singleton):

    def __init__(self):
        super().__init__()
        self.api_key = config.RANGO_API_KEY
        self.base_url = config.RANGO_BASE_URL
        self.__meta = None
        self._popular_tokens = None
        asyncio.run(self.post_init())

    async def post_init(self):
        url = f"meta"
        response_json: MetaResponse = await self.__request(url, "GET")
        response_obj: MetaResponse = MetaResponse.from_dict(response_json)
        self.__meta = response_obj
        params = {'excludeNonPopulars': True}
        popular_response_json: MetaResponse = await self.__request(url, "GET", extra_params=params)
        popular_response: MetaResponse = MetaResponse.from_dict(popular_response_json)
        self._popular_tokens = popular_response
        print('Meta has been initialized...')

    def __get_token_data(self, blockchain: str, token_address: Optional[str]):
        meta: MetaResponse = self.__meta
        for token in meta.tokens:
            if token.blockchain == blockchain.upper() and token.address == token_address.lower():
                return token

    async def get_meta(self) -> MetaResponse:
        return self.__meta

    async def popular_tokens(self):
        return self._popular_tokens['popularTokens']

    async def __request(self, url: str, method: str, data=None, extra_params=None, list_params=None) -> Any:
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
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.request(
                    method,
                    headers=headers,
                    url=req_url,
                    json=data
            ) as resp:
                response = await resp.json()
                return response

    async def balance(self, wallet_addresses: list[str]) -> BalanceResponse:
        url = f"wallets/details"
        list_params = []
        for bwa in wallet_addresses:
            list_params.append(f'address={bwa}')
        response_json: dict = await self.__request(url, "GET", list_params=list_params)
        balance_response: BalanceResponse = GetWalletDetailsResponse.from_dict(response_json)
        return balance_response

    async def route(self, _connected_wallets: list, selected_wallets: dict, from_blockchain: str,
                    from_token_address: str,
                    to_blockchain: str, to_token_address: str, amount: float) -> BestRouteResponse:
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
                "symbol": from_token.symbol,
                "address": from_token_address
            },
            "to": {
                "blockchain": to_blockchain.upper(),
                "symbol": to_token.symbol,
                "address": to_token_address
            },
            "checkPrerequisites": False,
            "connectedWallets": connected_wallets,
            "selectedWallets": selected_wallets,
            "amount": amount,
            "maxLength": 1
        }
        response_json: dict = await self.__request(url, "POST", data=payload)
        best_route: BestRouteResponse = BestRouteResponse.from_dict(response_json)
        return best_route

    async def create_transaction(self, request_id: str, step: int = 1, slippage: int = 2):
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
        return response

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

