# gh-codeql-summarize

This is the GitHub CodeQL Summarize project and Actions which allows users to generate Models as Data (MaD) from CodeQL databases.

## Run

### Actions

The main use case for `codeqlsummarize` is to run it as an Action so the purposes of automating this process.

```yml
- name: Generate CodeQL Summaries
  uses: advanced-security/codeql-summarize@v1
  with:
    # This file defines the projects you want to make sure to get the latest and greatest
    # summaries from.
    projects: ./projects.json
    # Token needs access to download the CodeQL databases you want to create summaries for
    token: ${{ secrets.CODEQL_SUMMARY_GENERATOR_TOKEN }}
```

### GH CLI

You can install this tool as part of the GitHub CLI using the following commands:

```bash
gh extensions install advanced-security/gh-codeql-summarize
gh codeql-summarize --help
```

### Manual Command Line

```bash
git clone https://github.com/advanced-security/gh-codeql-summarize.git && cd gh-codeql-summarize
python3 -m codeqlsummarize --help
```

## License

This project is licensed under the terms of the MIT open source license. Please refer to [MIT](./LICENSE.txt) for the full terms.

## Maintainers 

[CODEOWNERS](./.github/CODEOWNERS) file.

## Support

Please create issues for any feature requests, bugs, or documentation problems.

## Acknowledgement

- @GeekMasher - Author
- @zbazztian - Major contributor
