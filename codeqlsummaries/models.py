import os
from typing import *
from dataclasses import *

from requests import Session

CODEQL_LANGUAGES = ["java"]


@dataclass
class Summaries:
    rows: List[str]



@dataclass
class GitHub:
    endpoint: ClassVar[str] = "https://api.github.com"
    token: Optional[str]

    owner: Optional[str] = None
    repo: Optional[str] = None

    session: Session = Session()

    def __post_init__(self):
        self.session = Session() 
        self.session.headers = {
            "Accept": "application/vnd.github.v3+json"
        }      
        if self.token:
            self.session.headers.update(Authorization="token " + self.token)
        

@dataclass
class CodeQLDatabase:
    name: str
    path: str

    language: str

    repository: Optional[str] = None
    token: Optional[str] = None
    summaries: Dict[str, Summaries] = field(default_factory=dict)

    session: Session = Session()

    def __post_init__(self):
        if not os.path.exists(self.path) and not os.path.isdir(self.path):
            raise Exception("Database folder incorrect")
        # TODO: Check if actual CodeQL Database
        if self.language not in CODEQL_LANGUAGES:
            raise Exception("Language is not supported by CodeQL")

    @property
    def target(self):
        return f"{self.name}.qll"

    def downloadDatabase(self, github: GitHub, output: str):
        url = f"https://api.github.com/repos/{self.repository}/code-scanning/codeql/databases/{self.language}"
        
        self.session.headers.update(Accept="application/zip")

        # NOTE the stream=True parameter below
        with github.session.get(url, stream=True) as r:
            r.raise_for_status()
            with open(output, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    # If you have chunk encoded response uncomment if
                    # and set chunk_size parameter to None.
                    #if chunk: 
                    f.write(chunk)
        
        # TODO: Extract zip correctly

