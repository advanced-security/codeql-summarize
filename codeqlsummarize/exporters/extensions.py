import os
import yaml
import logging

from codeqlsummarize.models import CodeQLDatabase, GitHub

logger = logging.getLogger("codeqlsummarize.exporters.extensions")

CODEQL_EXTENSION = """\
  - addsTo:
      pack: codeql/{language}-queries
      extensible: {extensible}
    data:
{rows}
"""

EXTENSIBLE = {
    "SinkModel": "sinkModel",
    "SourceModel": "sourceModel",
    "SummaryModel": "summaryModel",
}


def exportDataExtensions(database: CodeQLDatabase, output: str, github: GitHub, **kargs):
    logger.info("Running export to Data Extensions")

    if database.language == "javascript":
        logger.warning("Skipping JavaScript for now")
        return

    # Get the CodeQL pack for the language
    codeqlPack = findCodeQLPack(output, database.language)
    os.makedirs(os.path.join(codeqlPack, "generated"), exist_ok=True)

    if database.owner:
        os.makedirs(os.path.join(codeqlPack, "generated", database.owner), exist_ok=True)
        extensions_file = os.path.join(codeqlPack, "generated", database.owner, f"{database.name}.yml")
    else:
        extensions_file = os.path.join(codeqlPack, "generated", f"{database.name}.yml")

    data = "extensions:\n"
    for sname, summary in database.summaries.items():
        if len(summary.rows) == 0:
            continue

        summary_rows = ""
        for mad in sorted(summary.rows):
            m = mad.split(";")
            summary_rows += "      - "
            summary_rows += f'["{m[0]}", "{m[1]}", {m[2]}, "{m[3]}", "{m[4]}", "{m[5]}", "{m[6]}", "{m[7]}", "{m[8]}"]\n'

        data += CODEQL_EXTENSION.format(
            rows=summary_rows,
            language=database.language,
            extensible=EXTENSIBLE.get(sname, "sinkModel")
        )

    logger.info(f"Writing Data Extensions to: {extensions_file}")
    with open(extensions_file, "w") as handle:
        handle.write(data)


def findCodeQLPack(location: str, language: str) -> str:
    """Find the CodeQL pack for the given language in the output directory"""

    if os.path.isfile(location):
        raise Exception(f"Directory {location} does not exist")

    for root, dirs, files in os.walk(location):
        for file in files:
            if file == "qlpack.yml":
                with open(os.path.join(root, file), "r") as f:
                    qlpack = yaml.safe_load(f)
                    
                    if f"codeql/{language}-queries" in qlpack.get("extensionTargets", []):
                        return root

    raise Exception(f"Could not find CodeQL pack for {language} in {location}")
