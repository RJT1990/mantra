IGNORED_FILES = ['__pycache__']
NO_OF_ARTEFACTS = 5
MANTRA_DEVELOPMENT_TAG_NAME = 'mantra dev'

DEFAULT_RESULT_README = '''# Result Showcase

Containing results from applying the [%s](/model/%s) model to the [%s](/data/%s) dataset.

## Instructions

```
mantra train %s --dataset %s %s
```

%s'''