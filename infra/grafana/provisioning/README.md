# Grafana Provisioning

Automatic provisioning configuration for Grafana dashboards and datasources. Enables infrastructure-as-code approach to monitoring setup with zero-manual configuration.

## Subdirectories

- **dashboards/** - Dashboard provisioning configuration
- **datasources/** - Datasource provisioning configuration

## How It Works

On Grafana startup:
1. Read provisioning YAML files from `dashboards/` and `datasources/`
2. Automatically create/update datasources
3. Auto-load dashboard JSON files from configured directories
4. Apply configurations idempotently (no duplicates)

## Benefits

- Version-controlled monitoring setup
- Reproducible Grafana instances
- Infrastructure as Code (IaC)
- Easy disaster recovery
- Consistent across environments (dev, staging, prod)

## Provisioning Flow

```
provisioning/
├── dashboards/
│   └── dashboards.yml          # Tells Grafana to load from ../dashboards/
└── datasources/
    └── datasources.yml         # Configures Prometheus, Loki, Tempo connections
                                  ↓
                            Grafana reads YAML on startup
                                  ↓
                         Auto-creates datasources & dashboards
                                  ↓
                         Available in Grafana UI immediately
```

## Editing Provisioned Resources

### Dashboards
- Edit JSON files in `../dashboards/`
- Restart Grafana to reload
- UI edits allowed but not persisted (recreate on restart)

### Datasources
- Edit YAML in `datasources/datasources.yml`
- Restart Grafana to apply changes
- UI changes overwritten on next restart

## Documentation

See subdirectories for detailed configuration:
- `dashboards/README.md` - Dashboard auto-loading setup
- `datasources/README.md` - Datasource connection configuration

See `../DEPLOYMENT.md` for:
- Adding new datasources
- Configuring authentication
- Customizing provisioning paths
