# Azure CI/CD

Gravitas uses the unreleased Azure deployment as its integration-test environment. A push to `main`, or a manual workflow dispatch, performs this sequence:

1. Authenticate to Azure through GitHub OpenID Connect.
2. Build commit-tagged API and worker images in Azure Container Registry.
3. Deploy new Azure Container Apps revisions and verify their image tags.
4. Build the web app with the deployed API URL and publish it to Azure Static Web Apps.
5. Run [the live environment test](../scripts/test_live_environment.py) against the deployed stack.

The live test loads the public web app, checks API health, submits a real render, waits for the Azure queue and worker, downloads through the API proxy, and verifies both required PNG dimensions.

## GitHub Environment

The workflow uses a GitHub environment named `azure-test` and requires these environment secrets:

| Secret | Purpose |
| --- | --- |
| `AZURE_CLIENT_ID` | Client ID of the user-assigned identity trusted by GitHub OIDC |
| `AZURE_TENANT_ID` | Microsoft Entra tenant containing the identity |
| `AZURE_SUBSCRIPTION_ID` | Subscription containing `rg-gravitas` |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | Deployment token for `swa-gravitas-434092` |

Read the repository's current OIDC subject prefix before creating the federated credential:

```powershell
$prefix = gh api repos/fabioc-aloha/gravitas/actions/oidc/customization/sub --jq .sub_claim_prefix
$subject = "$prefix`:environment:azure-test"
```

Use `$subject` exactly. GitHub may issue an immutable owner/repository-ID prefix rather than the legacy name-only prefix, and Azure requires an exact match. Scope the deployment identity to `rg-gravitas`. Do not use a client secret; `azure/login` exchanges GitHub's short-lived identity token through OIDC.

## Workflow

The deployment definition is [.github/workflows/deploy-and-test.yml](../.github/workflows/deploy-and-test.yml). It uses a single concurrency group with cancellation disabled because two deployments must not race on the shared environment.

The workflow does not run the local mock-backed suites. Its release assertion is the black-box test against deployed Azure resources. The local suites remain useful during development, but they are not the deployment gate.

## Manual Live Test

Use this only when diagnosing the environment or validating the gate itself:

```powershell
python scripts/test_live_environment.py `
  --web-url https://orange-wave-0893cf10f.7.azurestaticapps.net `
  --api-url https://ca-gravitas-api.ashypebble-8202f9e4.eastus.azurecontainerapps.io `
  --timeout-seconds 900
```

Each run creates a real render and incurs Azure compute and storage usage.

## Promotion Boundary

There is no production environment yet. Before release, create a separate production resource set and require approval before promotion. Do not repurpose this shared test environment as production without separating credentials, data, quotas, and deployment protection rules.
