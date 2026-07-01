# Setup Option

Using GitHub Actions

# Step 1: Output a Coverage report file in your CI

## Pytest [backend]

Install requirements in your terminal:

```bash
pip install pytest pytest-cov
```

In a GitHub Action, run tests and generate a coverage report:

```bash
pytest --cov --cov-branch --cov-report=xml
```

## Vitest [web]

Install requirements in your terminal:

```bash
npm install --save-dev vitest @vitest/coverage-v8
```

In a GitHub Action, run tests and generate a coverage report:

```bash
npx vitest run --coverage
```

## Mobile :

For your Flutter Mobile App: You don't need any of the ones you listed! Flutter has testing built-in. You just run flutter test --coverage, which generates an lcov.info file that Codecov will gladly accept.

# Step 2: Select an upload token to add as a secret on GitHub-optional

# Step 3: add token as repository secret

## CODECOV_TOKEN

Set in **GitHub → Settings → Secrets and variables → Actions** as `CODECOV_TOKEN`.
The actual token is **not** committed here.
Retrieve it from the Codecov project settings page if you need to rotate or re-add it.

# Step 4: Add Codecov to your GitHub Actions workflow yaml file

After tests run, this will upload your coverage report to Codecov:

```yaml
- name: Upload coverage reports to Codecov
  uses: codecov/codecov-action@v5
  with:
    token: ${{ secrets.CODECOV_TOKEN }}
```

Your final GitHub Actions workflow for a project using Pytest could look something like this:

```yaml
name: Run tests and upload coverage

on: push

jobs:
  test:
    name: Run tests and collect coverage
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 2

      - name: Set up Python
        uses: actions/setup-python@v4

      - name: Install dependencies
        run: pip install pytest pytest-cov

      - name: Run tests
        run: pytest --cov --cov-branch --cov-report=xml

      - name: Upload results to Codecov
        uses: codecov/codecov-action@v5
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
```
