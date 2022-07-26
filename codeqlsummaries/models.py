import os
import tarfile
import logging
from typing import *
from dataclasses import *

from requests import Session


CODEQL_LANGUAGES = ["java"]

logger = logging.getLogger("codeqlsummaries.models")


@dataclass
class Summaries:
    rows: List[str]


@dataclass
class GitHub:
    owner: str
    repo: str

    endpoint: ClassVar[str] = "https://api.github.com"
    token: Optional[str] = None

    session: Session = field(default=Session())

    def __post_init__(self):
        self.session = Session()
        self.session.headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            self.session.headers.update(Authorization="token " + self.token)


@dataclass
class CodeQLDatabase:
    name: str

    language: str

    path: Optional[str] = None
    repository: Optional[str] = None
    token: Optional[str] = None
    summaries: Dict[str, Summaries] = field(default_factory=dict)

    session: Session = Session()

    def __post_init__(self):
        if self.path and not os.path.exists(self.path):
            raise Exception("Database folder incorrect")
        
        if self.language not in CODEQL_LANGUAGES:
            raise Exception("Language is not supported by CodeQL")

    def exists(self) -> bool:
        return False if not self.path else os.path.exists(self.path)

    @property
    def target(self):
        return f"{self.name}.qll"

    @property
    def database_folder(self):
        if self.repository:
            return self.repository.replace("/", "_")
        # TODO
        return "temp_db"
            
    def downloadDatabase(self, github: GitHub, output: str) -> str:
        """ Download CodeQL database
        """
        url = f"https://api.github.com/repos/{self.repository}/code-scanning/codeql/databases/{self.language}"

        resp = self.session.get(url)
        if resp.status_code != 200:
            logger.warning("Failed to download CodeQL Database")
            logger.warning("Access control or missing database on GitHub instance")
            return ""

        self.session.headers.update(Accept="application/zip")

        output_zip = os.path.join(output, self.database_folder + ".tar.gz")
        output_db = os.path.join(output, self.database_folder)

        with github.session.get(url, stream=True) as r:
            r.raise_for_status()
            with open(output_zip, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    # If you have chunk encoded response uncomment if
                    # and set chunk_size parameter to None.
                    # if chunk:
                    f.write(chunk)

        tar = tarfile.open(output_zip)
        # SECURITY: Do we trust this DB?
        tar.extractall(output_db)

        return output_db

