# Dashboard Provisioning

Automatic dashboard loading configuration for Grafana. Enables dashboards to be version-controlled and deployed with infrastructure.

## Configuration File

- **dashboards.yml** - Tells Grafana which directories contain dashboard JSON files to auto-load

## How Dashboards Are Loaded

Grafana provisioning scans configured directories and:
1. Loads all `.json` files as dashboards
2. Creates/updates dashboards idempotently
3. Assigns UIDs for consistent identification
4. Applies folder organization

## Adding Dashboards

To add a new dashboard:

1. Create dashboard in Grafana UI or export existing dashboard JSON
2. Save JSON file to `../../dashboards/` directory:
   ```bash
   cp my-dashboard.json ../../dashboards/
   ```
3. Restart Grafana:
   ```bash
   docker-compose -f docker-compose.monitoring.yml restart grafana
   ```
4. Dashboard appears in Grafana UI under provisioned folder

## Dashboard Organization

Dashboards are organized by folder in the provisioning config:
- `../../dashboards/` - All dashboards auto-loaded into "Ecole Platform" folder
- Subfolder organization possible via dashboards.yml config

## Versioning

- All dashboard JSON files are version-controlled in git
- Changes to dashboards persist in JSON files
- Restart Grafana to apply JSON changes
- UI edits are not persisted unless exported back to JSON

## Best Practices

- Export dashboards regularly to JSON files
- Review JSON changes before committing
- Use meaningful dashboard names and descriptions
- Document dashboard purposes in README
- Test dashboards in dev environment before promoting to prod
- Use consistent UID naming conventions

## Troubleshooting

**Dashboards not appearing:**
- Check dashboards.yml references correct directory
- Verify JSON files are valid (use `jq` to validate)
- Review Grafana logs for load errors
- Ensure directory is readable by Grafana container

**Changes not persisting:**
- UI changes only apply until restart
- Export changed dashboards to JSON files
- Commit JSON files to git for persistence
