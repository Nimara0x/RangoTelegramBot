from dataclasses import dataclass, field
from typing import Optional, List
from dataclasses_json import dataclass_json, config
from decimal import Decimal


@dataclass_json
@dataclass
class ExplorerUrl:
    url: str
    description: str


@dataclass_json
@dataclass
class BridgeExtra:
    requireRefundAction: bool
    srcTx: str
    destTx: str


@dataclass_json
@dataclass
class TransactionObject:
    status: str
    timestamp: int
    outputAmount: str
    explorerUrl: List[ExplorerUrl]
    bridgeExtra: BridgeExtra
    extraMessage: Optional[str] = None
    failedType: Optional[str] = None
    referrals: Optional[str] = None
    newTx: Optional[str] = None
    diagnosisUrl: Optional[str] = None
    steps: Optional[str] = None
    outputToken: Optional[str] = None

    def is_successful(self) -> bool:
        return self.status == "success"

    def get_output_amount(self) -> str:
        return '%.3f' % Decimal(self.outputAmount)

    def print_explorer_urls(self):
        msg = ''
        for ex in self.explorerUrl:
            msg += f'🔹 [Explorer Link]({ex.url}) -> {ex.description} \n'
            return msg


@dataclass_json
@dataclass
class Amount:
    amount: int
    decimals: int


@dataclass_json
@dataclass
class Asset:
    blockchain: str
    symbol: str
    address: Optional[str] = None

    def __repr__(self):
        return f'{self.blockchain}.{self.symbol}'


@dataclass_json
@dataclass
class SwapFee:
    asset: Asset
    expenseType: str
    amount: float
    name: str



@dataclass_json
@dataclass
class SwapNode:
    marketName: str
    percent: float


@dataclass_json
@dataclass
class SwapResultAsset:
    symbol: str
    logo: str
    blockchainLogo: str
    blockchain: str
    decimals: int
    usdPrice: Optional[float] = None
    address: Optional[str] = None


@dataclass_json
@dataclass
class RecommendedSlippage:
    error: bool
    slippage: Optional[float] = None


@dataclass_json
@dataclass
class SwapResult:
    swapperId: str
    swapperLogo: str
    swapperType: str
    from_: SwapResultAsset = field(metadata=config(field_name='from'))
    to: SwapResultAsset
    fromAmount: float
    toAmount: float
    fee: List[SwapFee]
    estimatedTimeInSeconds: int
    swapChainType: str
    routes: Optional[List[SwapNode]] = None
    recommendedSlippage: Optional[RecommendedSlippage] = None


@dataclass_json
@dataclass
class SimulationResult:
    outputAmount: float
    swaps: List[SwapResult]
    resultType: str


@dataclass
@dataclass_json
class BestRouteResponse:
    requestAmount: float
    requestId: str
    result: SimulationResult
    walletNotSupportingFromBlockchain: bool
    processingLimitReached: bool
    missingBlockchains: List[str]
    diagnosisMessages: List[str]
    compareStatus: str
    from_: Asset = field(metadata=config(field_name='from'))
    to: Asset
