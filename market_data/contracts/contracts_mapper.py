class ContractMapper:

    def __init__(self):
        self._projectx_to_internal: dict[str, str] = {}
        self._internal_to_projectx: dict[str, str] = {}

    def add(
        self,
        internal_contract: str,
        projectx_contract_id: str,
    ) -> None:

        self._internal_to_projectx[
            internal_contract
        ] = projectx_contract_id

        self._projectx_to_internal[
            projectx_contract_id
        ] = internal_contract

    def map_contract(
        self,
        contract: str,
    ) -> None:

        projectx_id = self.resolve_contract(contract)

        self._contract_mapper.add(
            internal_contract=contract,
            projectx_contract_id=projectx_id,
        )

        print(
            f"Contract mapping: "
            f"{contract} → {projectx_id}"
        )
    def to_projectx(
        self,
        internal_contract: str,
    ) -> str:

        try:
            return self._internal_to_projectx[
                internal_contract
            ]

        except KeyError:
            raise ValueError(
                f"No ProjectX mapping for "
                f"contract: {internal_contract}"
            )

    def from_projectx(
        self,
        projectx_contract_id: str,
    ) -> str:

        try:
            return self._projectx_to_internal[
                projectx_contract_id
            ]

        except KeyError:
            raise ValueError(
                f"No internal mapping for "
                f"ProjectX contract: {projectx_contract_id}"
            )