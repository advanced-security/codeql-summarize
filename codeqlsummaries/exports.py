import json
import logging
from dataclasses import asdict
from codeqlsummaries.models import CodeQLDatabase, GitHub


logger = logging.getLogger("codeqlsummaries.exporters")


def exportToJson(database: CodeQLDatabase, output: str, **kargs):
    logger.info("Running export to JSON")
    data = {}
    for name, summary in database.summaries.items():
        data[name] = summary.rows

    with open(output, "w") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)

    logger.info("Completed writing to output")

    return


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


def exportCustomizations(database: CodeQLDatabase, output: str, github: GitHub = None, **kargs):
    logger.info(f"Running export customizations")
    padding = " " * 6

    models = {}

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
            name=database.name, type=sname, models=sname, rows=rows
        )

        models[sname] = custom

    # lib code
    data = CODEQL_LIBRARY.format(language=database.language, **models)
    

    # Path to store libs
    root = f"{database.language}/{github.owner}"
    # Create
    sub = f"{github.owner}/{database.language}/Customizations.qll"

    # CodeQL package file

    # Generate Customizations.qll

    with open(output, "w") as handle:
        handle.write(data)
