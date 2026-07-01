# Backend (Python, FastAPI)

## Install

Install `sentry-sdk` from PyPI:

```bash
pip install "sentry-sdk" "fastapi"
```

## Configure SDK

If you have the `fastapi` package in your dependencies, the FastAPI integration will be enabled automatically when you initialize the Sentry SDK. Initialize the Sentry SDK before your app has been initialized:

```python


from fastapi import FastAPI
import sentry_sdk

sentry_sdk.init(
    dsn=os.environ["SENTRY_DSN"],  # populated from Doppler dev / .env
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
    # Enable sending logs to Sentry
    enable_logs=True,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    # Set profile_session_sample_rate to 1.0 to profile 100%
    # of profile sessions.
    profile_session_sample_rate=1.0,
    # Set profile_lifecycle to "trace" to automatically
    # run the profiler on when there is an active transaction
    profile_lifecycle="trace",
)

app = FastAPI()

```

Alternatively, you can also explicitly control continuous profiling or use transaction profiling. See our [documentation](https://docs.sentry.io/platforms/python/profiling/) for more information.

The above configuration captures both error and performance data. To reduce the volume of performance data captured, change `traces_sample_rate` to a value between 0 and 1.

## Verify

You can easily verify your Sentry installation by creating a route that triggers an error:

```python

@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0

```

You can send logs to Sentry using the Sentry logging APIs:

```python
import sentry_sdk

# Send logs directly to Sentry
sentry_sdk.logger.info('This is an info log message')
sentry_sdk.logger.warning('This is a warning message')
sentry_sdk.logger.error('This is an error message')
```

You can also use Python's built-in logging module, which will automatically forward logs to Sentry:

```python
import logging

# Your existing logging setup
logger = logging.getLogger(__name__)

# These logs will be automatically sent to Sentry
logger.info('This will be sent to Sentry')
logger.warning('User login failed')
logger.error('Something went wrong')
```

Send test metrics from your app to verify metrics are arriving in Sentry.

```python
from sentry_sdk import metrics

# Emit metrics
metrics.count("checkout.failed", 1)
metrics.gauge("queue.depth", 42)
metrics.distribution("cart.amount_usd", 187.5)
```

When you open [http://localhost:8000/sentry-debug/](http://localhost:8000/sentry-debug/) with your browser, a transaction in the Performance section of Sentry will be created.Additionally, an error event will be sent to Sentry and will be connected to the transaction.It takes a couple of moments for the data to appear in Sentry.

### DSN

Not committed. Retrieve from <https://ensmr.sentry.io> → project `ecole-backend` → Settings → Client Keys (DSN).
Synced into Doppler `dev` config as `SENTRY_DSN`.

# Web (React)

## Install

npm install --save @sentry/react

## Configure SDK

import \* as Sentry from "@sentry/react";

Sentry.init({
dsn: import.meta.env.VITE_SENTRY_DSN, // populated from Doppler dev / .env
// Setting this option to true will send default PII data to Sentry.
// For example, automatic IP address collection on events
sendDefaultPii: true,
integrations: [
Sentry.browserTracingIntegration(),
Sentry.replayIntegration()
],
// Tracing
tracesSampleRate: 1.0, // Capture 100% of the transactions
// Set 'tracePropagationTargets' to control for which URLs distributed tracing should be enabled
tracePropagationTargets: ["localhost", /^https:\/\/yourserver\.io\/api/],
// Session Replay
replaysSessionSampleRate: 0.1, // This sets the sample rate at 10%. You may want to change it to 100% while in development and then sample at a lower rate in production.
replaysOnErrorSampleRate: 1.0 // If you're not already sampling the entire session, change the sample rate to 100% when sampling sessions where errors occur.,
// Enable logs to be sent to Sentry
enableLogs: true
});

const container = document.getElementById("app");
const root = createRoot(container);
root.render(<App />);

### DSN

Not committed. Retrieve from <https://ensmr.sentry.io> → project `ecole-web` → Settings → Client Keys (DSN).
Synced into Doppler `dev` config as `VITE_SENTRY_DSN`.

## Upload Source Maps

npx @sentry/wizard@latest -i sourcemaps --saas --org ensmr --project ecole-web

## AI-Assisted Setup

Read and follow: https://github.com/getsentry/sentry-for-ai/blob/main/skills/sentry-react-sdk/SKILL.md

## Verify

import \* as Sentry from '@sentry/react';
// Add this button component to your app to test Sentry's error tracking
function ErrorButton() {
return (
<button
onClick={() => {
// Send a log before throwing the error
Sentry.logger.info('User triggered test error', {
action: 'test_error_button_click',
});
// Send a test metric before throwing the error
Sentry.metrics.count('test_counter', 1);
throw new Error('This is your first error!');
}} >
Break the world
</button>
);
}

# Mobile (Flutter)

## Automatic Configuration (Recommended)

Add Sentry automatically to your app with the [Sentry wizard](https://docs.sentry.io/platforms/flutter/#install) (call this inside your project directory).

```bash
brew install getsentry/tools/sentry-wizard && sentry-wizard -i flutter --saas --org ensmr --project ecole-mobile
```

The Sentry wizard will automatically patch your project with the following:

- Configure the SDK with your DSN and performance monitoring options in your `main.dart` file.
- Update your `pubspec.yaml` with the Sentry package
- Add an example error to verify your setup

## Manual Configuration

Alternatively, you can also set up the SDK manually, by following the [manual setup docs](https://docs.sentry.io/platforms/flutter/manual-setup/).

If you already have the configuration for Sentry in your application, and just need this project's (ecole-mobile) DSN:

Not committed. Retrieve from <https://ensmr.sentry.io> → project `ecole-mobile` → Settings → Client Keys (DSN).
Synced into Doppler `dev` config as `MOBILE_SENTRY_DSN` (legacy fallback `SENTRY_DSN` still read by `mobile/lib/main.dart`).

## Verify

Create an intentional error, so you can test that everything is working. In the example below, pressing the button will throw an exception:

```dart

import 'package:sentry/sentry.dart';

child: ElevatedButton(
  onPressed: () {
    throw StateError('This is test exception');
  },
  child: const Text('Verify Sentry Setup'),
)

```

### DSN

Not committed. Retrieve from the Sentry mobile project as described above.
