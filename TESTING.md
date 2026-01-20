# Valkey Bundle - Testing Guide

## Python Entrypoint

The Docker entrypoint has been rewritten in Python for better testability and maintainability.

### Features

- **Module Auto-Discovery**: Automatically loads all `.so` modules from `/usr/lib/valkey/`
- **Configurable Arguments**: Module-specific arguments via environment variables
- **Debug Mode**: Set `DEBUG=1` to see the generated command
- **Testable**: Comprehensive unit tests with pytest support

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SEARCH_MODULE_ARGS` | Arguments for libsearch.so | `--use-coordinator yes --reader-threads 8` |
| `JSON_MODULE_ARGS` | Arguments for libjson.so | `--json-depth 128` |
| `BLOOM_MODULE_ARGS` | Arguments for libvalkey_bloom.so | `--bloom-capacity 1000` |
| `LDAP_MODULE_ARGS` | Arguments for libvalkey_ldap.so | `--ldap-server ldap://host` |
| `VALKEY_EXTRA_FLAGS` | Additional valkey-server flags | `--maxmemory 2gb` |
| `MODULE_DIR` | Module directory path | `/usr/lib/valkey` (default) |
| `DEBUG` | Enable debug output | `1` |

### Usage Examples

#### Default (no custom args)
```bash
docker run ghcr.io/kailas-cloud/valkey-bundle:9.0-coordinator
```

#### With Coordinator Enabled
```bash
docker run -e SEARCH_MODULE_ARGS="--use-coordinator yes --reader-threads 8" \
  ghcr.io/kailas-cloud/valkey-bundle:9.0-coordinator
```

#### Multiple Module Args
```bash
docker run \
  -e SEARCH_MODULE_ARGS="--use-coordinator yes" \
  -e JSON_MODULE_ARGS="--json-depth 128" \
  -e VALKEY_EXTRA_FLAGS="--maxmemory 2gb" \
  ghcr.io/kailas-cloud/valkey-bundle:9.0-coordinator
```

#### Debug Mode
```bash
docker run -e DEBUG=1 -e SEARCH_MODULE_ARGS="--use-coordinator yes" \
  ghcr.io/kailas-cloud/valkey-bundle:9.0-coordinator
```

## Running Tests

### Prerequisites
```bash
# Optional: Install pytest for full test suite
pip install pytest
```

### Run Tests
```bash
# Run all tests
python3 test_entrypoint.py

# Or with pytest (if installed)
pytest test_entrypoint.py -v
```

### Test Coverage

The test suite covers:
- ✅ Module discovery (empty dir, non-existent dir, with files)
- ✅ Module argument parsing from environment
- ✅ Command generation with/without module args
- ✅ Extra flags handling
- ✅ Full integration test with all features

### Example Test Output
```
✅ Discovered 2 modules: ['libjson.so', 'libsearch.so']
✅ Generated module args: ['--loadmodule', '/tmp/xxx/libjson.so', '--loadmodule', '/tmp/xxx/libsearch.so', '--use-coordinator', 'yes']

✅ Basic tests passed!
```

## Development

### Testing Locally (without Docker)

The Python entrypoint can be tested locally without building Docker images:

```bash
# Create a test module directory
mkdir -p /tmp/test-modules
touch /tmp/test-modules/libsearch.so
touch /tmp/test-modules/libjson.so

# Test with DEBUG mode
MODULE_DIR=/tmp/test-modules \
SEARCH_MODULE_ARGS="--use-coordinator yes" \
DEBUG=1 \
python3 9.0/debian/bundle-docker-entrypoint.py valkey-server
```

### Modifying the Entrypoint

1. Edit `9.0/debian/bundle-docker-entrypoint.py`
2. Run tests: `python3 test_entrypoint.py`
3. Build and test Docker image
4. Commit changes

## Kubernetes Deployment

Example StatefulSet with coordinator:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: valkey
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: valkey
        image: ghcr.io/kailas-cloud/valkey-bundle:9.0-coordinator
        env:
        - name: SEARCH_MODULE_ARGS
          value: "--use-coordinator yes --reader-threads 8 --writer-threads 4"
```

## Troubleshooting

### Module Not Loading

Enable debug mode to see the exact command:
```bash
docker run -e DEBUG=1 ghcr.io/kailas-cloud/valkey-bundle:9.0-coordinator
```

### Wrong Arguments Format

Module arguments must start with `--`:
- ✅ Correct: `--use-coordinator yes`
- ❌ Wrong: `use-coordinator yes`

### Check Available Modules

```bash
docker run --entrypoint ls ghcr.io/kailas-cloud/valkey-bundle:9.0-coordinator /usr/lib/valkey/
```

## CI/CD

GitHub Actions automatically builds and publishes the image when changes are pushed to `mainline` branch.

Tags generated:
- `mainline` - latest build from mainline branch
- `9.0-coordinator` - coordinator-enabled build
- `latest` - latest stable release

## Contributing

When adding new modules:
1. Update `9.0/debian/Dockerfile` to build the module
2. Add module to `get_module_args()` in `bundle-docker-entrypoint.py`
3. Add tests in `test_entrypoint.py`
4. Update this documentation
