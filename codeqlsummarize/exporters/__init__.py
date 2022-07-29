from codeqlsummarize.exporters.exptjson import exportToJson
from codeqlsummarize.exporters.customizations import exportBundle, exportCustomizations

EXPORTERS = {
    "json": exportToJson,
    "customizations": exportCustomizations,
    "bundle": exportBundle,
}
