import os
from typing import *
from dataclasses import *


CODEQL_LANGUAGES = ["java"]


@dataclass
class Summaries:
    rows: List[str]


@dataclass
class CodeQLDatabase:
    name: str
    path: str

    language: str

    summaries: Dict[str, Summaries] = field(default_factory=dict)

    def __post_init__(self):
        if not os.path.exists(self.path) and not os.path.isdir(self.path):
            raise Exception("Database folder incorrect")
        # TODO: Check if actual CodeQL Database
        if self.language not in CODEQL_LANGUAGES:
            raise Exception("Language is not supported by CodeQL")

    @property
    def target(self):
        return f"{self.name}.qll"

    def downloadDatabase(self, repository: str):
        owner, repo = repository.split("/", 1)

        raise Exception("Feature not built")
