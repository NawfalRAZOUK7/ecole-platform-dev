# Quickstart

Send a test email to ibatt.test@inbox.testmail.app and then click here to retrieve the email via our simple JSON API. If you don't see it immediately, hit refresh.

Next: explore the documentation to learn about querying spam reports, filtering emails by tag, and more. If you want the most feature-rich API and you're familiar with GraphQL, check out the GraphQL Playground.

# Namespaces

ibatt
Send emails to ibatt.{tag}@inbox.testmail.app

## Copy Me

ibatt

# API keys

The actual API key is **not** committed in this repo.
Retrieve it from <https://testmail.app/console> after activating your account via the GitHub Student Pack.

## Storage

- **Local dev:** add to your local `.env` as `TESTMAIL_API_KEY=<your-key>` (file is gitignored).
- **Doppler dev:** already synced — verify with `doppler secrets get TESTMAIL_API_KEY --config dev`.
- **CI (GitHub Actions):** add as `TESTMAIL_API_KEY` repository secret if E2E email tests are run from CI.

## API Header format

```http
Authorization: Bearer <TESTMAIL_API_KEY>
```
