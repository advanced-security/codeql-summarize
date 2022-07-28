# File from CodeQL GitHub repo
# https://github.com/github/codeql/blob/main/misc/scripts/models-as-data/generate_flow_model.py

import json
import os
import os.path
import glob
import shlex
import subprocess
import tempfile
import logging
from typing import *

from codeqlsummaries import __MODULE_PATH__
from codeqlsummaries.models import CodeQLDatabase, Summaries

logger = logging.getLogger("codeqlsummaries.generator")


# https://github.com/github/codeql/tree/main/java/ql/src/utils/model-generator
QUERIES = {
    "SinkModel": "CaptureSinkModels.ql",
    "SourceModel": "CaptureSourceModels.ql",
    "SummaryModel": "CaptureSummaryModels.ql",
}


class Generator:
    CODEQL_LOCATION = os.path.realpath(os.path.join(__MODULE_PATH__, "..", "codeql"))
    CODEQL_REPO = "https://github.com/github/codeql.git"

    TEMP_PATH = os.path.join(tempfile.gettempdir(), "codeqlsummaries")

    codeql_cli: Optional[str] = None

    def __init__(self, database: CodeQLDatabase):
        self.database = database

        self.codeql_cli = self.findCodeQLCli()

    @staticmethod
    def getCodeQLRepo():
        if os.path.exists(Generator.CODEQL_LOCATION):
            logger.warning(f"CodeQL already exists, not getting latest...")
            return

        logger.info(f"Downloading CodeQL repo to :: {Generator.CODEQL_LOCATION}")
        cmd = [
            "git",
            "clone",
            "--depth",
            "1",
            Generator.CODEQL_REPO,
            Generator.CODEQL_LOCATION,
        ]
        with open(os.devnull, "w") as null:
            ret = subprocess.call(cmd, stdout=null, stderr=null)
            if ret != 0:
                raise Exception("Error getting CodeQL repo")
        return Generator

    def findCodeQLCli(self) -> str:
        actions = glob.glob(
            os.path.join(
                os.environ.get("RUNNER_TOOL_CACHE", ""),
                "CodeQL",
                "*",
                "x64",
                "codeql",
                "codeql" + ("" if os.name == "posix" else ".exe"),
            )
        )
        if len(actions) != 0:
            logger.debug(f"CodeQL found on Actions :: {actions[0]}")
            return actions[0]
        logger.debug(f"Use CodeQL default")
        return "codeql"

    def getModelGeneratorQuery(self, name) -> Optional[str]:
        logger.info(f"Finding query name: {name}")
        query_path = None
        # Find in CodeQL
        query_file = QUERIES.get(name)

        if query_file:
            query_path = f"{Generator.CODEQL_LOCATION}/{self.database.language}/ql/src/utils/model-generator/{query_file}"
            if os.path.exists(query_path):
                return query_path

        # Find in this repo
        return

    def runQuery(self, query: str) -> Summaries:
        logger.info("Running Query :: " + query)
        resultBqrs = os.path.join(Generator.TEMP_PATH, "out.bqrs")
        output_std = os.path.join(Generator.TEMP_PATH, "runquery.txt")

        cmd = [
            self.codeql_cli,
            "query",
            "run",
            query,
            "--database",
            self.database.path,
            "--output",
            resultBqrs,
            "--threads",
            "8",
        ]

        with open(output_std, "w") as std:
            ret = subprocess.call(cmd, stdout=std, stderr=std)
            if ret != 0:
                logger.error(f"See log file: {output_std}")
                raise Exception("Failed to generate " + query)

        rows = self.readRows(resultBqrs)

        return Summaries(rows)

    def readRows(self, bqrsFile):
        logger.debug(f"Processing rows")
        # //"package;type;overrides;name;signature;ext;spec;kind"
        generatedJson = os.path.join(Generator.TEMP_PATH, "out.json")
        output_std = os.path.join(Generator.TEMP_PATH, "rows.txt")

        cmd = [
            self.codeql_cli,
            "bqrs",
            "decode",
            bqrsFile,
            "--format=json",
            "--output",
            generatedJson,
        ]

        with open(output_std, "w") as std:
            ret = subprocess.call(cmd, stdout=std, stderr=std)
            if ret != 0:
                logger.error(f"See log file: {output_std}")
                raise Exception(
                    "Failed to decode BQRS. Failed command was: " + shlex.join(cmd)
                )

        logger.debug(f"writing json output to: {generatedJson}")
        with open(generatedJson) as f:
            results = json.load(f)

        try:
            results["#select"]["tuples"]
        except KeyError:
            raise Exception("Unexpected JSON output - no tuples found")

        rows = []
        for tup in results["#select"]["tuples"]:
            rows.extend(tup)

        logger.debug(f"Final Row Summary count: {len(rows)}")

        return rows
