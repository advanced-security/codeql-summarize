import os
import json
import logging
import tempfile
from argparse import ArgumentParser

from codeqlsummaries import __MODULE_PATH__
from codeqlsummaries.generator import Generator, QUERIES
from codeqlsummaries.models import CodeQLDatabase, GitHub
from codeqlsummaries.exporters import EXPORTERS

logger = logging.getLogger("main")


parser = ArgumentParser("codeqlsummaries", "CodeQL Summary Generator")
parser.add_argument(
    "--debug", action="store_true", default=bool(os.environ.get("DEBUG"))
)
parser.add_argument(
    "-f",
    "--format",
    default="bundle",
    help="Export format (`json`, `customizations`, `mad`, `bundle`)",
)
parser.add_argument("-i", "--input", help="Input / Project File")
parser.add_argument("-o", "--output", default=os.getcwd(), help="Output DIR")
parser.add_argument("--working", default=os.getcwd(), help="Working directory of the generator")

parser.add_argument("--disable-cache", action="store_true")

parser_codeql = parser.add_argument_group("CodeQL")
parser_codeql.add_argument("--codeql-base", default="./codeql", help="CodeQL Base Path")
parser_codeql.add_argument("-p", "--project-repo", help="Project Repo")
parser_codeql.add_argument("-db", "--database", help="CodeQL Database Location")
parser_codeql.add_argument("-l", "--language", help="CodeQL Database Language")

parser_github = parser.add_argument_group("GitHub")
parser_github.add_argument(
    "-r",
    "--github-repository",
    default=os.environ.get("GITHUB_REPOSITORY"),
    help="GitHb Repository",
)
parser_github.add_argument(
    "-t", "--github-token", default=os.environ.get("GITHUB_TOKEN")
)


if __name__ == "__main__":
    arguments = parser.parse_args()

    github = None
    databases = []

    logging.basicConfig(
        level=logging.DEBUG if arguments.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.debug("Debugging is enabled")

    if not arguments.format:
        raise Exception("Format flag is not set")

    if not EXPORTERS.get(arguments.format):
        raise Exception(f"Format mode provided isn't valid: {arguments.format}")

    # Support for Actions temp dirs
    temppath = os.path.join(
        os.environ.get("RUNNER_TEMP", tempfile.gettempdir()), "codeqlsummaries"
    )
    os.makedirs(temppath, exist_ok=True)
    Generator.TEMP_PATH = temppath

    if arguments.github_repository:
        owner, repo = arguments.github_repository.split("/", 1)
        logger.info(f"GitHub repo present - Owner: {owner}, Repository: {repo}")

        github = GitHub(owner=owner, repo=repo, token=arguments.github_token)

    if not os.path.exists(Generator.CODEQL_LOCATION):
        Generator.getCodeQLRepo()

    if arguments.output:
        logger.debug(f"Creating output dir :: {arguments.output}")
        os.makedirs(arguments.output, exist_ok=True)
    else:
        raise Exception("Output is not set")
    
    # If scan repo settings are present
    if github and arguments.project_repo and arguments.language:
        logger.info(f"Analysing remote repo: {arguments.project_repo} ({arguments.language})")
        _, repo = arguments.project_repo.split("/", 1)
        database = CodeQLDatabase(
            repo,
            language=arguments.language,
            repository=arguments.project_repo
        )
        database.path = database.downloadDatabase(github, temppath)

        databases.append(database)

    # If a project file is present
    elif arguments.input and os.path.exists(arguments.input):
        """Input file is a `projects.json` file"""
        logger.info(f"Loaded input / projects file :: {arguments.input}")

        if not os.path.exists(arguments.input):
            raise Exception("Input file is invalid")
        with open(arguments.input, "r") as handle:
            projects = json.load(handle)

        for lang, repos in projects.items():
            for repo in repos:
                _, name = repo.split("/")

                db = CodeQLDatabase(name=name, language=lang, repository=repo)

                if github and db.repository:
                    logger.info(f"Downloading database for :: {repo}")

                    download_path = db.downloadDatabase(
                        github, temppath, use_cache=not arguments.disable_cache
                    )

                    db.path = download_path

                if not db.path:
                    logger.warning(f"CodeQL Database path is not set")

                databases.append(db)

        logger.info("Finished loading databases from input file")

    elif arguments.database and arguments.language:
        # find local db + language
        database = CodeQLDatabase("test", path=arguments.database, language=arguments.language)
        databases.append(database)

        logger.info("Finished loading database from path")

    else:
        raise Exception("Failed to set mode of analysis")

    logger.info(f"Databases to process :: {len(databases)}")

    for database in databases:
        logger.info(f"Database setup complete: {database}")

        if not database.exists():
            raise Exception("CodeQL Database does not exist...")

        # find codeql
        generator = Generator(database)

        # generate models
        # https://github.com/github/codeql/blob/main/misc/scripts/models-as-data/generate_flow_model.py

        for name, query in QUERIES.items():
            query_path = generator.getModelGeneratorQuery(name)
            if not query_path:
                continue
            database.summaries[name] = generator.runQuery(query_path)

        for summary, data in database.summaries.items():
            logger.info(f" Summary('{summary}', rows='{len(data.rows)}')")

        logger.info(f"Running exporter :: {arguments.format}")

        exporter = EXPORTERS.get(arguments.format)
        if not exporter:
            raise Exception("Unknown or Unsupported exporter")

        exporter(database, arguments.output, github=github, working=arguments.working)
