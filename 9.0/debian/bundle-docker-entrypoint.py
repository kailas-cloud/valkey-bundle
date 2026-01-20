#!/usr/bin/env python3
"""
Valkey Bundle Docker Entrypoint
Loads Valkey modules with configurable arguments
"""
import os
import sys
import glob
from pathlib import Path


def get_module_args():
    """Get module-specific arguments from environment variables"""
    return {
        'libsearch.so': os.getenv('SEARCH_MODULE_ARGS', ''),
        'libjson.so': os.getenv('JSON_MODULE_ARGS', ''),
        'libvalkey_bloom.so': os.getenv('BLOOM_MODULE_ARGS', ''),
        'libvalkey_ldap.so': os.getenv('LDAP_MODULE_ARGS', ''),
    }


def discover_modules(module_dir='/usr/lib/valkey'):
    """Discover all .so modules in the module directory"""
    module_path = Path(module_dir)
    if not module_path.exists():
        return []
    
    return sorted(module_path.glob('*.so'))


def build_module_args(modules, module_args_map):
    """Build --loadmodule arguments for all discovered modules"""
    args = []
    
    for module in modules:
        module_name = module.name
        module_specific_args = module_args_map.get(module_name, '')
        
        args.append('--loadmodule')
        args.append(str(module))
        
        # Add module-specific arguments if configured
        if module_specific_args:
            args.extend(module_specific_args.split())
    
    return args


def get_extra_args():
    """Get extra Valkey flags from environment"""
    extra = os.getenv('VALKEY_EXTRA_FLAGS', '')
    return extra.split() if extra else []


def drop_privileges():
    """Drop privileges to valkey user if running as root"""
    if os.geteuid() == 0:
        try:
            import pwd
            import grp
            
            valkey_user = pwd.getpwnam('valkey')
            valkey_group = grp.getgrnam('valkey')
            
            # Change ownership of current directory
            os.system(f'find . ! -user valkey -exec chown valkey {{}} +')
            
            # Drop privileges
            os.setgroups([])
            os.setgid(valkey_group.gr_gid)
            os.setuid(valkey_user.pw_uid)
            
            print(f"Dropped privileges to user 'valkey' (uid={valkey_user.pw_uid})")
        except (KeyError, OSError) as e:
            print(f"Warning: Could not drop privileges: {e}", file=sys.stderr)


def main():
    """Main entrypoint logic"""
    args = sys.argv[1:]
    
    if not args:
        print("Error: No command specified", file=sys.stderr)
        sys.exit(1)
    
    # Check if first arg is a flag or config file
    first_arg = args[0]
    if first_arg.startswith('-') or first_arg.endswith('.conf'):
        # Prepend valkey-server
        args = ['valkey-server'] + args
    
    # If not calling valkey-server, just exec the command
    if args[0] != 'valkey-server':
        os.execvp(args[0], args)
        return
    
    # Drop privileges if running as root
    drop_privileges()
    
    # Set restrictive umask
    current_umask = os.umask(0)
    os.umask(current_umask)
    if current_umask == 0o022:
        os.umask(0o077)
    
    # Build command with modules
    module_dir = os.getenv('MODULE_DIR', '/usr/lib/valkey')
    modules = discover_modules(module_dir)
    module_args_map = get_module_args()
    
    # Build final command
    cmd = ['valkey-server']
    cmd.extend(args[1:])  # User args (e.g., config file)
    cmd.extend(build_module_args(modules, module_args_map))  # Module args
    cmd.extend(get_extra_args())  # Extra flags
    
    # Debug output (if DEBUG env var is set)
    if os.getenv('DEBUG'):
        print(f"DEBUG: Module directory: {module_dir}", file=sys.stderr)
        print(f"DEBUG: Found modules: {[m.name for m in modules]}", file=sys.stderr)
        print(f"DEBUG: Final command: {' '.join(cmd)}", file=sys.stderr)
    
    # Execute valkey-server
    os.execvp('valkey-server', cmd)


if __name__ == '__main__':
    main()
