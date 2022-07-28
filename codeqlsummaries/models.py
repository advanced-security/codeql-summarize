import os
import zipfile
import logging
import tempfile
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


@dataclass
class CodeQLDatabase:
    name: str

    language: str

    path: Optional[str] = None
    repository: Optional[str] = None
    token: Optional[str] = None
    summaries: Dict[str, Summaries] = field(default_factory=dict)

    tmp: ClassVar[str] = tempfile.gettempdir()

    session: Session = Session()

    def __post_init__(self):
        if self.path and not os.path.exists(self.path):
            raise Exception("Database folder incorrect")
       
        if self.language not in CODEQL_LANGUAGES:
            raise Exception("Language is not supported by CodeQL Summary Generator")

    def exists(self) -> bool:
        return False if not self.path else os.path.exists(self.path)

    @property
    def display_name(self):
        new_name = self.name.replace("-", " ")
        return new_name.title().replace(" ", "")

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

        if not github or not github.token:
            raise Exception("Failed to download due to authorization")

        headers = {
            "Accept": "application/zip",
            "Authorization": f"token {github.token}",
        }

        output_zip = os.path.join(output, self.database_folder + ".tar.gz")
        output_db = os.path.join(output, self.database_folder)
        
        if not os.path.exists(output_zip):
            logger.info("Downloading CodeQL Database from GitHub")
            with github.session.get(url, headers=headers, stream=True, allow_redirects=True) as r:
                r.raise_for_status()
                with open(output_zip, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        # If you have chunk encoded response uncomment if
                        # and set chunk_size parameter to None.
                        # if chunk:
                        f.write(chunk)
        else:
            logger.info("Database archive is present on system, skipping download...")

        logger.info(f"Extracting archive data :: {output_zip}")
        
        # SECURITY: Do we trust this DB?
        with zipfile.ZipFile(output_zip) as zf:
            zf.extractall(output_db)

        return os.path.join(output_db, self.language)

