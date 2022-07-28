# File from CodeQL GitHub repo
# https://github.com/github/codeql/blob/main/misc/scripts/models-as-data/generate_flow_model.py

import json
import os
import os.path
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

    def __init__(self, database: CodeQLDatabase):
        self.database = database
        # working temp dir


    def getCodeQLRepo(self):
        if os.path.exists(Generator.CODEQL_LOCATION):
            # TODO: Update to latest?
            return
        cmd = [
            "git",
            "clone",
            "--depth",
            "1",
            Generator.CODEQL_REPO,
            Generator.CODEQL_LOCATION,
        ]
        with open(os.devnull, "w") as null:
            ret = subprocess.run(cmd, stdout=null)
            if ret != 0:
                raise Exception("Error getting CodeQL repo")
        return Generator

    def getModelGeneratorQuery(self, name) -> Optional[str]:
        logger.info(f"Finding query name: {name}")
        query_path = None
        # Find in CodeQL
        query_file = QUERIES.get(name)

        if query_file:
            query_path = f"{Generator.CODEQL_LOCATION}/{self.database.language}/ql/src/utils/model-generator/{query_file}"
            logger.debug(f"Query path :: {query_path}")
            if os.path.exists(query_path):
                return query_path

        # Find in this repo

        return

    def runQuery(self, query: str) -> Summaries:
        logger.info("Running Query :: " + query)
        resultBqrs = os.path.join(Generator.TEMP_PATH, "out.bqrs")
        cmd = [
            "codeql",
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

        ret = subprocess.call(cmd)
        if ret != 0:
            raise Exception("Failed to generate " + query)

        rows = self.readRows(resultBqrs)

        return Summaries(rows)

    def readRows(self, bqrsFile):
        # //"package;type;overrides;name;signature;ext;spec;kind"
        generatedJson = os.path.join(Generator.TEMP_PATH, "out.json")
        cmd = [
            "codeql",
            "bqrs",
            "decode",
            bqrsFile,
            "--format=json",
            "--output",
            generatedJson,
        ]
        ret = subprocess.call(cmd)
        if ret != 0:
            raise Exception(
                "Failed to decode BQRS. Failed command was: " + shlex.join(cmd)
            )

        with open(generatedJson) as f:
            results = json.load(f)

        try:
            results["#select"]["tuples"]
        except KeyError:
            raise Exception("Unexpected JSON output - no tuples found")

        rows = []
        for tup in results["#select"]["tuples"]:
            rows.extend(tup)

        return rows
