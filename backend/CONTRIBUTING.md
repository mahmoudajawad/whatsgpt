# Contributing Guidelines

Start with creating a `venv` for isolated development:
```bash
# From project root
python -m venv venv
# Activate venv using your OS method
source venv/bin/activate
```

Install all development requirements using:
```bash
pip install -r dev_requirements.txt
```

Install all runtime requirements using:
```bash
pip install -r requirements.txt
```

From the same shell start your preferred editor.


## Guidelines

- Address all errors, warnings raised by `mypy`, `pylint` during development. Don't commit a file that includes errors or warning.
- Use [`reST`](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html) to document your work.
- Always format your files before committing using `black` and invoke `isort` to sort imports correctly.
- Always suffix commit messages of changes to Backend with `backend: ` followed with the message.
