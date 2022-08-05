import os
import json
import logging
from dataclasses import asdict

from codeqlsummarize.models import CodeQLDatabase, GitHub
from codeqlsummarize.generator import QUERIES
from codeqlsummarize.utils import findCodeQLCli

logger = logging.getLogger("codeqlsummarize.exporters")


CODEQL_LIBRARY = """\
import {language}
private import semmle.code.{language}.dataflow.ExternalFlow

{SinkModel}
{SourceModel}
{SummaryModel}
"""

CODEQL_CUSTOMIZATION = """\
private class {name}{type}Custom extends {models}Csv {{
  override predicate row(string row) {{
    row = [
{rows}
    ]
  }}
}}
"""


def saveQLL(
    database: CodeQLDatabase, output_customizations: str, github: GitHub, **kargs
):
    padding = " " * 6
    owner = github.owner.replace("-", "_").lower()

    models = {}
    # initially populate data
    for key in QUERIES.keys():
        models[key] = "// NOT SET"

    for sname, summary in database.summaries.items():
        rows = ""
        counter = 1

        if len(summary.rows) == 0:
            models[sname] = f"// No {sname} found\n"
            continue
        for mad in sorted(summary.rows):
            rows += f'{padding}"{mad}"'

            if len(summary.rows) > counter:
                rows += ",\n"
            counter += 1

        # generate codeql lib for dabase
        custom = CODEQL_CUSTOMIZATION.format(
            name=database.display_name(owner=owner),
            type=sname,
            models=sname,
            rows=rows,
        )

        models[sname] = custom

    logger.debug(f"List of models: {models.keys()}")

    # Generate Customizations.qll
    data = CODEQL_LIBRARY.format(language=database.language, **models)

    with open(output_customizations, "w") as handle:
        handle.write(data)

    return


def exportCustomizations(
    database: CodeQLDatabase, output: str, github: GitHub, **kargs
):
    logger.info(f"Running export customizations")
    if not output.endswith(".qll"):
        raise Exception(f"CodeQL customizations file does not endwith `.qll`")

    saveQLL(database, output, github=github, **kargs)

    return


CODEQL_LOCK = """\
---
dependencies:
  codeql/{language}-all:
    version: 0.0.12
compiled: false
lockVersion: 1.0.0
"""
CODEQL_PACK = """\
name: {owner}/{language}
version: {version}
dependencies:
  codeql/{language}-all: "*"
library: true
extractor: {language}
"""

CODEQL_CUSTOMIZATIONS_QLL = """\
// This file is Automatically Generated based on the files in-side this relative
// directory. This makes it easier to automate this process.
import {language}

module {owner} {{
{custom}
}}
"""


def exportBundle(database: CodeQLDatabase, output: str, github: GitHub, **kargs):
    logger.debug(f"Output directory :: {output}")
      
    owner = github.owner.replace("-", "_").lower()
    
    if not github or not github.owner:
        raise Exception("Failed to export Bundle: No owner / repo name set")

    codeql_pack_path = f"{database.language}-summarize"
    codeql_pack_name = f"{owner}/{codeql_pack_path}"

    # Create root for language
    root = os.path.join(output, codeql_pack_path)

    codeql = findCodeQLCli()

    if not os.path.exists(root) and codeql:
        logger.info("Generating CodeQL Summarize Pack")
        codeql("pack", "init", "--version=0.0.1", "--extractor", database.language, codeql_pack_path, cwd=output)

    if not os.path.exists(os.path.join(root, "qlpack.yml")):
        raise Exception("Pack wasn't found")

    # Create README
    readme = os.path.join(root, "README.md")
    if not os.path.exists(readme):
        with open(readme, "w") as handle:
            handle.write("# CodeQL Summarize Pack\n")

    logger.debug(f"Root Pack Path :: {root}")

    # Create language subfolder (if needed)
    sub = os.path.join(root, owner, codeql_pack_path.replace("-", "_"))
    logger.debug(f"Checking sub pack path exists: {sub}")
    os.makedirs(sub, exist_ok=True)

    name = database.display_name(owner=owner) + "Generated"

    db_custom_lib_path = os.path.join(sub, name + ".qll")
    saveQLL(database, db_custom_lib_path, github)

    # Dynamically update Customizations.qll
    customizations_path = os.path.join(sub, "Customizations.qll")
    customizations_data = ""
    
    codeql_files = os.listdir(sub)
    if not codeql_files:
        logger.error(f"This is a major issue and please report in the GitHub issues")
        raise Exception("Something is really wrong here...")

    for custom in codeql_files:
        if custom == "Customizations.qll":
            continue
        
        custom = custom.replace(".qll", "")

        impt = f"    private import {owner}.{database.language}_summarize.{custom}\n"
        customizations_data += impt

    with open(customizations_path, "w") as handle:
        handle.write(
            CODEQL_CUSTOMIZATIONS_QLL.format(
                language=database.language,
                custom=customizations_data,
                owner=owner,
            )
        )

    return
