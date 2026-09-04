from abc import ABC, abstractmethod

from data.models.contract import Contract


class ContractRepository(ABC):

    @abstractmethod
    def save(self, contracts: list[Contract]) -> None:
        pass

    @abstractmethod
    def get(self, contract: str) -> Contract | None:
        pass

    @abstractmethod
    def get_front_month(
        self,
        instrument: str,
    ) -> Contract | None:
        pass

    @abstractmethod
    def get_all(self, instrument: str) -> list[Contract]:
        pass

    @abstractmethod
    def get_next_contract(
        self,
        instrument: str,
        contract: str,
    ) -> Contract | None:
        pass