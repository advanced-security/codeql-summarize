
import os
from argparse import ArgumentParser


from codeqlsummaries.generator import Generator, CODEQL_LANGUAGES, QUERIES
from codeqlsummaries.models import *


parser = ArgumentParser("codeqlsummaries", "CodeQL Summary Generator")
parser.add_argument(
    "--debug", action="store_true", default=bool(os.environ.get("DEBUG"))
)


parser_codeql = parser.add_argument_group("CodeQL")
parser_codeql.add_argument("-db", "--database", help="CodeQL Database Location")
parser_codeql.add_argument("-l", "--language", help="CodeQL Database Language")

parser_github = parser.add_argument_group("GitHub")
parser_github.add_argument("-r", "--repository", default=os.environ.get("GITHUB_REPOSITORY"), help="GitHb Repository")
parser_github.add_argument("--github-token", default=os.environ.get("GITHUB_TOKEN"))


if __name__ == "__main__":
    arguments = parser.parse_args()
    
    # find db + language
    database = CodeQLDatabase("test", arguments.database, arguments.language)

    # find codeql 
    generator = Generator(database)

    # generate models
    # https://github.com/github/codeql/blob/main/misc/scripts/models-as-data/generate_flow_model.py
    query = generator.getModelGeneratorQuery("sinks")
    for name, query in QUERIES.items(): 
        database.summaries[name] = generator.runQuery(query)


    # Export to Customizations.qll file / MaD YM 
    


