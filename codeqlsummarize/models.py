import os
import zipfile
import logging
import tempfile
import shutil
from typing import *
from dataclasses import *

from codeqlsummarize.utils import request


CODEQL_LANGUAGES = ["java", "csharp"]

logger = logging.getLogger("codeqlsummarize.models")


@dataclass
class Summaries:
    rows: List[str] = field(default_factory=list)


@dataclass
class GitHub:
    owner: str = "security"
    repo: str = "codeql"

    endpoint: ClassVar[str] = "https://api.github.com"
    token: Optional[str] = None

    def __post_init__(self):
        if not self.token:
            logger.warning("GitHub Token is not set, API access will be unavailable")
        else:
            logger.debug(f"GitHub Token is set")

    @property
    def available(self):
        return self.token is not None


@dataclass
class CodeQLDatabase:
    name: str

    language: str

    path: Optional[str] = None
    repository: Optional[str] = None
    summaries: Dict[str, Summaries] = field(default_factory=dict)

    def __post_init__(self):
        if self.path and not os.path.exists(self.path):
            raise Exception("Database folder incorrect")

        if self.language not in CODEQL_LANGUAGES:
            raise Exception("Language is not supported by CodeQL Summary Generator")

    def exists(self) -> bool:
        return False if not self.path else os.path.exists(self.path)

    def display_name(self, owner: Optional[str] = None) -> str:
        if self.repository:
            r = self.repository.replace("-", " ")
            own, repo = r.split("/", 1)
            if owner and owner == own:
                return repo.title().replace(" ", "")

            return f"{own.title()}{repo.title()}".replace(" ", "")
        new_name = self.name.replace("-", " ")
        return new_name.title().replace(" ", "")

    @property
    def owner(self) -> Optional[str]:
        if self.repository:
            o, n = self.repository.split("/", 1)
            return o
        return

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

            with request(
                url,
                headers=headers,
                method="get",
            ) as r:
                with open(output_zip, "wb") as f:
                    while True:
                        chunk = r.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)

        else:
            logger.info("Database archive is present on system, skipping download...")

        logger.info(f"Extracting archive data :: {output_zip}")

        # SECURITY: Do we trust this DB?
        with zipfile.ZipFile(output_zip) as zf:
            zf.extractall(output_db)

        logger.info(f" >>> {output_db}")
        codeql_lang_path = os.path.join(output_db, self.language)
        if os.path.exists(codeql_lang_path):
            return codeql_lang_path

        for codeql_dir in os.listdir(output_db):
            codeql_dir = os.path.join(output_db, codeql_dir)
            if os.path.isdir(codeql_dir):
                return codeql_dir
