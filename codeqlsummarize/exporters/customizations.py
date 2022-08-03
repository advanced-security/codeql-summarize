import os
import json
import logging
from dataclasses import asdict

from codeqlsummarize.models import CodeQLDatabase, GitHub
from codeqlsummarize.generator import QUERIES

logger = logging.getLogger("codeqlsummarize.exporters")


CODEQL_LIBRARY = """\
import {language}
private import semmle.code.{language}.dataflow.ExternalFlow

{SinkModel}
{SourceModel}
{SummaryModel}
"""

CODEQL_CUSTOMIZATION = """\
private class {name}{type}Custom extends {models} {{
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
    owner = github.owner.replace("-", "_")

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
        for mad in summary.rows:
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
// This file is Automatically Generated
import {language}

module {owner} {{
{custom}
}}
"""


def exportBundle(database: CodeQLDatabase, output: str, github: GitHub, **kargs):
    logger.debug(f"Output directory :: {output}")

    owner = github.owner.replace("-", "_")

    if not github or not github.owner:
        raise Exception("Failed to export Bundle: No owner / repo name set")

    # Create root for language
    root = os.path.join(output, database.language, owner)
    os.makedirs(root, exist_ok=True)
    logger.debug(f"Root for language :: {root}")

    # Create language files
    codeql_lang_lock = os.path.join(root, "codeql-pack.lock.yml")
    if not os.path.exists(codeql_lang_lock):
        logger.debug(f"Creating Language Lock file :: {codeql_lang_lock}")
        with open(codeql_lang_lock, "w") as handle:
            handle.write(CODEQL_LOCK.format(language=database.language))

    codeql_lang_pack = os.path.join(root, "qlpack.yml")
    if not os.path.exists(codeql_lang_pack):
        logger.debug(f"Creating Language Pack file :: {codeql_lang_pack}")
        with open(codeql_lang_pack, "w") as handle:
            handle.write(
                CODEQL_PACK.format(
                    owner=owner, version="0.1.0", language=database.language
                )
            )

    # Create language subfolder (if needed)
    sub = os.path.join(root, owner, database.language)
    os.makedirs(sub, exist_ok=True)

    name = database.display_name(owner=owner) + "Generated"

    db_custom_lib_path = os.path.join(sub, name + ".qll")
    saveQLL(database, db_custom_lib_path, github)

    # Dynamically update Customizations.qll
    customizations_path = os.path.join(sub, "Customizations.qll")
    customizations_data = ""
    for custom in os.listdir(sub):
        if custom == "Customizations.qll":
            continue

        impt = f"    private import {owner}.{database.language}.{name}\n"
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
