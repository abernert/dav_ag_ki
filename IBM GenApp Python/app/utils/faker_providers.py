from __future__ import annotations

from faker.providers import BaseProvider
from . import datasets


class GenappProvider(BaseProvider):
    def genapp_first_name(self) -> str:
        return datasets.random_first_name(self.random)

    def genapp_last_name(self) -> str:
        return datasets.random_surname(self.random)

    def genapp_postcode(self) -> str:
        return datasets.random_postcode(self.random)
