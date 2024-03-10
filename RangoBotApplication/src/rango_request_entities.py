from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from dataclasses_json import dataclass_json, config


@dataclass_json
@dataclass
class Asset:
    blockchain: str
    symbol: str
    address: Optional[str] = None


@dataclass_json
@dataclass
class Amount:
    amount: int
    decimals: int


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
    marketId: Optional[str] = None


@dataclass_json
@dataclass
class SwapResultAsset:
    symbol: str
    logo: str
    blockchainLogo: str
    blockchain: str
    decimals: int
    address: Optional[str] = None
    usdPrice: Optional[float] = None


@dataclass_json
@dataclass
class RecommendedSlippage:
    error: bool
    slippage: Optional[float] = None


@dataclass_json
@dataclass
class SwapRoute:
    nodes: List[SwapNode]


@dataclass_json
@dataclass
class SwapResult:
    swapperId: str
    swapperType: str
    from_: SwapResultAsset = field(metadata=config(field_name='from'))
    to: SwapResultAsset
    fromAmount: float
    toAmount: float
    fee: List[SwapFee]
    estimatedTimeInSeconds: int
    swapChainType: str
    fromAsset: Optional[Asset] = None
    toAsset: Optional[Asset] = None
    swapperLogo: Optional[str] = None
    fromAmountPrecision: Optional[float] = None
    fromAmountMinValue: Optional[float] = None
    fromAmountMaxValue: Optional[float] = None
    fromAmountRestrictionType: Optional[str] = None
    routes: Optional[List[SwapRoute]] = None
    recommendedSlippage: Optional[RecommendedSlippage] = None
    warnings: Optional[List[str]] = None
    timeStat: Optional[Dict[str, int]] = None
    includesDestinationTx: Optional[bool] = None
    maxRequiredSign: Optional[int] = None
    isWrapped: Optional[bool] = None


@dataclass_json
@dataclass
class SimulationResult:
    outputAmount: float
    swaps: List[SwapResult]
    resultType: str


@dataclass_json
@dataclass
class BlockchainValidationStatus:
    blockchain: str
    wallets: List[Dict[str, Any]]


@dataclass_json
@dataclass
class BestRouteRequest:
    from_: Asset = field(metadata=config(field_name='from'))
    to: Asset
    amount: str
    connectedWallets: Optional[List[Dict[str, Any]]] = None
    selectedWallets: Optional[Dict[str, str]] = None
    destination: Optional[str] = None
    checkPrerequisites: Optional[bool] = None
    affiliateRef: Optional[str] = None
    affiliateWallets: Optional[Dict[str, str]] = None
    affiliatePercent: Optional[float] = None
    transactionTypes: Optional[List[str]] = None
    swappers: Optional[List[str]] = None
    swappersExclude: Optional[bool] = None
    swapperGroups: Optional[List[str]] = None
    swappersGroupsExclude: Optional[bool] = None
    blockchains: Optional[List[str]] = None
    blockchainsExclude: Optional[bool] = None
    disableMultiStepTx: Optional[bool] = None
    maxLength: Optional[int] = None
    intraChainMessage: Optional[Dict[str, Any]] = None
    messagingProtocols: Optional[List[str]] = None
    contractCall: Optional[bool] = None
    slippage: Optional[float] = None


@dataclass_json
@dataclass
class BestRouteResponse:
    from_: Asset = field(metadata=config(field_name='from'))
    to: Asset
    requestAmount: float
    requestId: str
    result: SimulationResult
    walletNotSupportingFromBlockchain: bool
    processingLimitReached: bool
    missingBlockchains: List[str]
    diagnosisMessages: List[str]
    compareStatus: str
    validationStatus: Optional[List[BlockchainValidationStatus]] = None
