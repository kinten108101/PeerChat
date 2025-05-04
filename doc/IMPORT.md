The majority of the source code is written in Python. According to Python, there are many supported import styles. For the sake of readability, only a selected set of styles are allowed for this source code.

There should be two import styles:
- Named class import: `from lib.server import Server`
- Default import: `import lib.dotenv`. Notice: when using the exports of this module, you will have to write the full import path e.g. `lib.dotenv.source()`

## Debunking

You must not alias. For example, `import lib.dotenv as dotenv` is not allowed. The reader will be confused as to whether `dotenv` is a local variable or a module.

When writing named imports, only class imports are allowed. Functions and constants are not allowed. For example, `from lib.dotenv import source` is not allowed. The reader will be confused as to whether `source` is a local function or an imported function.
