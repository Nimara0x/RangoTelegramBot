from dataclasses import dataclass
from typing import Optional, List
from dataclasses_json import dataclass_json
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
