# Valkey Bundle with Module Args Support

Fork of [valkey-io/valkey-bundle](https://github.com/valkey-io/valkey-bundle) with configurable module arguments.

## Key Feature: Coordinator Support

This build enables `use-coordinator yes` for valkey-search module by default, which is required for cluster mode with cross-shard search.

## Usage

### Docker Run (with coordinator enabled)

```bash
docker run -d \
  --name valkey \
  -p 6379:6379 \
  -e SEARCH_MODULE_ARGS="use-coordinator yes" \
  ghcr.io/kailas-cloud/valkey-bundle:latest
```

### Docker Compose

```yaml
services:
  valkey:
    image: ghcr.io/kailas-cloud/valkey-bundle:latest
    environment:
      - SEARCH_MODULE_ARGS=use-coordinator yes reader-threads 8 writer-threads 4
    ports:
      - "6379:6379"
    volumes:
      - valkey-data:/data

volumes:
  valkey-data:
```

### Build with Custom Args

```bash
docker build \
  --build-arg SEARCH_MODULE_ARGS="use-coordinator yes reader-threads 16" \
  -t my-valkey-bundle \
  ./9.0/debian
```

## Module Arguments

Supported environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `SEARCH_MODULE_ARGS` | Arguments for valkey-search | `use-coordinator yes` |
| `JSON_MODULE_ARGS` | Arguments for valkey-json | |
| `BLOOM_MODULE_ARGS` | Arguments for valkey-bloom | |
| `LDAP_MODULE_ARGS` | Arguments for valkey-ldap | |
| `VALKEY_EXTRA_FLAGS` | Extra valkey-server flags | `--maxmemory 2gb` |

## Included Modules

- **valkey-search** 1.0.2 - Vector similarity search (coordinator enabled)
- **valkey-json** 1.0.2 - Native JSON support
- **valkey-bloom** 1.0.0 - Bloom filters
- **valkey-ldap** 1.0.0 - LDAP authentication

## License

BSD-3-Clause (same as Valkey)
