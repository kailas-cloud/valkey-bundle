#!/usr/bin/env python3
"""
Unit tests for bundle-docker-entrypoint.py
"""
import os
import sys
import tempfile
from pathlib import Path

try:
    import pytest
except ImportError:
    pytest = None

# Import the entrypoint module
sys.path.insert(0, str(Path(__file__).parent / '9.0' / 'debian'))
import bundle_docker_entrypoint as entrypoint


class TestModuleDiscovery:
    """Test module discovery functionality"""
    
    def test_discover_modules_empty_dir(self, tmp_path):
        """Test with empty module directory"""
        modules = entrypoint.discover_modules(str(tmp_path))
        assert modules == []
    
    def test_discover_modules_nonexistent_dir(self):
        """Test with non-existent directory"""
        modules = entrypoint.discover_modules('/nonexistent/path')
        assert modules == []
    
    def test_discover_modules_with_files(self, tmp_path):
        """Test discovering .so modules"""
        # Create dummy module files
        (tmp_path / 'libsearch.so').touch()
        (tmp_path / 'libjson.so').touch()
        (tmp_path / 'libbloom.so').touch()
        (tmp_path / 'not_a_module.txt').touch()
        
        modules = entrypoint.discover_modules(str(tmp_path))
        
        assert len(modules) == 3
        assert all(m.suffix == '.so' for m in modules)
        assert sorted([m.name for m in modules]) == ['libbloom.so', 'libjson.so', 'libsearch.so']


class TestModuleArgs:
    """Test module argument building"""
    
    def test_get_module_args_default(self):
        """Test default (empty) module args"""
        # Clear environment
        for key in ['SEARCH_MODULE_ARGS', 'JSON_MODULE_ARGS', 'BLOOM_MODULE_ARGS', 'LDAP_MODULE_ARGS']:
            os.environ.pop(key, None)
        
        args = entrypoint.get_module_args()
        assert all(v == '' for v in args.values())
    
    def test_get_module_args_with_env(self, monkeypatch):
        """Test module args from environment"""
        monkeypatch.setenv('SEARCH_MODULE_ARGS', '--use-coordinator yes --reader-threads 8')
        monkeypatch.setenv('JSON_MODULE_ARGS', '--json-depth 128')
        
        args = entrypoint.get_module_args()
        
        assert args['libsearch.so'] == '--use-coordinator yes --reader-threads 8'
        assert args['libjson.so'] == '--json-depth 128'
        assert args['libvalkey_bloom.so'] == ''
    
    def test_build_module_args_no_modules(self):
        """Test building args with no modules"""
        args = entrypoint.build_module_args([], {})
        assert args == []
    
    def test_build_module_args_without_specific_args(self, tmp_path):
        """Test building args without module-specific arguments"""
        module1 = tmp_path / 'libsearch.so'
        module2 = tmp_path / 'libjson.so'
        module1.touch()
        module2.touch()
        
        modules = [module1, module2]
        args_map = {}
        
        args = entrypoint.build_module_args(modules, args_map)
        
        expected = [
            '--loadmodule', str(module1),
            '--loadmodule', str(module2),
        ]
        assert args == expected
    
    def test_build_module_args_with_specific_args(self, tmp_path):
        """Test building args with module-specific arguments"""
        search_module = tmp_path / 'libsearch.so'
        json_module = tmp_path / 'libjson.so'
        search_module.touch()
        json_module.touch()
        
        modules = [search_module, json_module]
        args_map = {
            'libsearch.so': '--use-coordinator yes --reader-threads 8',
            'libjson.so': '--json-depth 128',
        }
        
        args = entrypoint.build_module_args(modules, args_map)
        
        expected = [
            '--loadmodule', str(search_module),
            '--use-coordinator', 'yes', '--reader-threads', '8',
            '--loadmodule', str(json_module),
            '--json-depth', '128',
        ]
        assert args == expected


class TestExtraArgs:
    """Test extra arguments functionality"""
    
    def test_get_extra_args_empty(self, monkeypatch):
        """Test with no extra args"""
        monkeypatch.delenv('VALKEY_EXTRA_FLAGS', raising=False)
        args = entrypoint.get_extra_args()
        assert args == []
    
    def test_get_extra_args_with_flags(self, monkeypatch):
        """Test with extra flags"""
        monkeypatch.setenv('VALKEY_EXTRA_FLAGS', '--maxmemory 2gb --maxmemory-policy allkeys-lru')
        args = entrypoint.get_extra_args()
        assert args == ['--maxmemory', '2gb', '--maxmemory-policy', 'allkeys-lru']


class TestIntegration:
    """Integration tests"""
    
    def test_full_command_generation(self, tmp_path, monkeypatch):
        """Test full command generation with all features"""
        # Setup module directory
        module_dir = tmp_path / 'modules'
        module_dir.mkdir()
        (module_dir / 'libsearch.so').touch()
        (module_dir / 'libjson.so').touch()
        
        # Setup environment
        monkeypatch.setenv('MODULE_DIR', str(module_dir))
        monkeypatch.setenv('SEARCH_MODULE_ARGS', '--use-coordinator yes --reader-threads 8')
        monkeypatch.setenv('VALKEY_EXTRA_FLAGS', '--maxmemory 1gb')
        
        # Get all components
        modules = entrypoint.discover_modules(str(module_dir))
        module_args_map = entrypoint.get_module_args()
        module_args = entrypoint.build_module_args(modules, module_args_map)
        extra_args = entrypoint.get_extra_args()
        
        # Build final command
        cmd = ['valkey-server']
        cmd.extend(module_args)
        cmd.extend(extra_args)
        
        # Verify command structure
        assert cmd[0] == 'valkey-server'
        assert '--loadmodule' in cmd
        assert '--use-coordinator' in cmd
        assert 'yes' in cmd
        assert '--reader-threads' in cmd
        assert '8' in cmd
        assert '--maxmemory' in cmd
        assert '1gb' in cmd
        
        # Verify order: modules first, then extra args
        loadmodule_indices = [i for i, x in enumerate(cmd) if x == '--loadmodule']
        maxmemory_index = cmd.index('--maxmemory')
        assert all(i < maxmemory_index for i in loadmodule_indices)


def test_run_tests():
    """Run all tests"""
    import subprocess
    result = subprocess.run(
        ['python3', '-m', 'pytest', __file__, '-v', '--tb=short'],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode


if __name__ == '__main__':
    # Run with pytest if available, otherwise print message
    try:
        import pytest
        sys.exit(pytest.main([__file__, '-v']))
    except ImportError:
        print("pytest not installed. Install with: pip install pytest")
        print("Running basic tests manually...")
        
        # Run a simple smoke test
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / 'libsearch.so').touch()
            (tmp_path / 'libjson.so').touch()
            
            modules = entrypoint.discover_modules(str(tmp_path))
            print(f"✅ Discovered {len(modules)} modules: {[m.name for m in modules]}")
            
            os.environ['SEARCH_MODULE_ARGS'] = '--use-coordinator yes'
            args_map = entrypoint.get_module_args()
            module_args = entrypoint.build_module_args(modules, args_map)
            print(f"✅ Generated module args: {module_args}")
            
            print("\n✅ Basic tests passed!")
