import os
import logging
from argparse import ArgumentParser

from codeqlsummaries import __MODULE_PATH__
from codeqlsummaries.generator import Generator, QUERIES
from codeqlsummaries.models import CodeQLDatabase, CODEQL_LANGUAGES
from codeqlsummaries.exports import *

logger = logging.getLogger("main")

EXPORTERS = {"json": exportToJson}

parser = ArgumentParser("codeqlsummaries", "CodeQL Summary Generator")
parser.add_argument(
    "--debug", action="store_true", default=bool(os.environ.get("DEBUG"))
)
parser.add_argument("-m", "--mode", type=str, help="Mode to run the tool in")
parser.add_argument(
    "-f",
    "--format",
    default="customizations",
    help="Export format (`customizations`, `mad`, `bundle`)",
)
parser.add_argument("-o", "--output")
parser.add_argument("--working", default=os.getcwd())

parser_codeql = parser.add_argument_group("CodeQL")
parser_codeql.add_argument("-db", "--database", help="CodeQL Database Location")
parser_codeql.add_argument("-l", "--language", help="CodeQL Database Language")

parser_github = parser.add_argument_group("GitHub")
parser_github.add_argument(
    "-r",
    "--repository",
    default=os.environ.get("GITHUB_REPOSITORY"),
    help="GitHb Repository",
)
parser_github.add_argument("--github-token", default=os.environ.get("GITHUB_TOKEN"))

if __name__ == "__main__":
    arguments = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if arguments.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # find db + language
    if not arguments.database:
        raise Exception("Database not set")

    database = CodeQLDatabase("test", arguments.database, arguments.language)

    logger.info(f"Database setup complete: {database}")

    # find codeql
    generator = Generator(database)

    # generate models
    # https://github.com/github/codeql/blob/main/misc/scripts/models-as-data/generate_flow_model.py

    for name, query in QUERIES.items():
        query_path = generator.getModelGeneratorQuery(name)

        database.summaries[name] = generator.runQuery(query_path)

        # temp
        for summary, data in database.summaries.items():
            logger.info(f" Summary('{summary}', rows='{len(data.rows)}')")

            with open("./test.txt", "w") as handle:
                handle.writelines(data.rows)

    # Export to Customizations.qll file / MaD YM

    if not arguments.output:
        raise Exception("Output not set")
    exporter = EXPORTERS.get(arguments.format)
    if not exporter:
        raise Exception("Unknown or Unsupported exporter")

    exporter(database, arguments.output)
