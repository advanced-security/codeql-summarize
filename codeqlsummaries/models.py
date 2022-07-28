import os
import zipfile
import logging
import tempfile
import shutil
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
        if not self.token:
            logger.warning("GitHub Token is not set, API access will be unavailable")
        else:
            logger.debug(f"GitHub Token is set")


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

    def downloadDatabase(
        self, github: GitHub, output: str, use_cache: bool = True
    ) -> str:
        """Download CodeQL database"""
        url = f"{GitHub.endpoint}/repos/{self.repository}/code-scanning/codeql/databases/{self.language}"
        logger.debug(f"Endpoint to Download Database :: {url}")

        if not github or not github.token:
            logger.error("GitHub or GitHub Token isn't valid...")
            logger.debug(github)
            raise Exception("Failed to download due to authorization")

        headers = {
            "Accept": "application/zip",
            "Authorization": f"token {github.token}",
        }

        if not os.path.exists(output):
            raise Exception(f"Output / Temp path does not exist: {output}")

        output_zip = os.path.join(output, self.database_folder + ".tar.gz")
        output_db = os.path.join(output, self.database_folder)

        # Deleting cached files
        if not use_cache:
            logger.info(f"Deleting cached files...")
            if os.path.exists(output_db):
                shutil.rmtree(output_db)

            if os.path.exists(output_zip):
                os.remove(output_zip)

        if not os.path.exists(output_zip):
            logger.info("Downloading CodeQL Database from GitHub")

            with github.session.get(
                url, headers=headers, stream=True, allow_redirects=True
            ) as r:
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
