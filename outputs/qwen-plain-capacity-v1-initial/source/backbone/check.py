"""Enforce the backbone boundary.

    python -m backbone.check --project backend scripts tests   (CI)
    python -m backbone.check --stamp                           (after bumping VERSION)

1. backbone/ imports only the standard library, itself, torch, transformers and huggingface_hub.
2. Project code imports the backbone only through its public names: from backbone import <name in __all__>.
3. backbone/ files match MANIFEST.json for the current VERSION. A change needs a version bump and a
   re-stamp; the same MANIFEST.json in another repository proves an identical copy.
"""
import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MANIFEST = HERE / 'MANIFEST.json'
ALLOWED_PACKAGES = {'backbone', 'torch', 'transformers', 'huggingface_hub'}


def file_hashes():
    files = (p for p in HERE.rglob('*') if p.is_file() and p != MANIFEST and '__pycache__' not in p.parts)
    return {p.relative_to(HERE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


def imports(path):
    for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name, None
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            yield node.lineno, node.module, [alias.name for alias in node.names]


def backbone_errors():
    errors = []
    for path in sorted(HERE.rglob('*.py')):
        for line, module, _ in imports(path):
            top = module.split('.')[0]
            if top not in sys.stdlib_module_names and top not in ALLOWED_PACKAGES:
                errors.append(f'backbone/{path.relative_to(HERE)}:{line} imports {module}; '
                              'the backbone may not depend on project code or other packages')
    return errors


def project_errors(dirs):
    import backbone
    public = set(backbone.__all__)
    errors = []
    for folder in dirs:
        for path in sorted((ROOT / folder).rglob('*.py')):
            for line, module, names in imports(path):
                where = f'{path.relative_to(ROOT)}:{line}'
                if module.startswith('backbone.'):
                    errors.append(f'{where} imports {module}; use "from backbone import ..." instead')
                elif module == 'backbone' and names:
                    for name in names:
                        if name not in public:
                            errors.append(f'{where} imports backbone.{name}, which is not public')
    return errors


def manifest_errors():
    version = (HERE / 'VERSION').read_text().strip()
    if not MANIFEST.exists():
        return ['backbone/MANIFEST.json is missing; run python -m backbone.check --stamp']
    recorded = json.loads(MANIFEST.read_text())
    if recorded['version'] != version:
        return [f'backbone/VERSION is {version} but MANIFEST.json records {recorded["version"]}; '
                'run python -m backbone.check --stamp']
    current = file_hashes()
    changed = sorted(f for f in current.keys() | recorded['files'].keys() if current.get(f) != recorded['files'].get(f))
    if changed:
        return ['backbone changed without a version bump: ' + ', '.join(changed) +
                '. Bump backbone/VERSION, then run python -m backbone.check --stamp']
    return []


def stamp():
    version = (HERE / 'VERSION').read_text().strip()
    current = file_hashes()
    if MANIFEST.exists():
        recorded = json.loads(MANIFEST.read_text())
        if recorded['version'] == version and recorded['files'] != current:
            sys.exit('backbone files changed: bump backbone/VERSION before stamping')
    MANIFEST.write_text(json.dumps({'version': version, 'files': current}, indent=2) + '\n')
    print(f'Stamped backbone {version} ({len(current)} files).')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--stamp', action='store_true')
    parser.add_argument('--project', nargs='*', default=['backend', 'scripts'])
    args = parser.parse_args()
    if args.stamp:
        stamp()
        sys.exit()
    problems = backbone_errors() + project_errors(args.project) + manifest_errors()
    for problem in problems:
        print('BOUNDARY:', problem)
    if problems:
        sys.exit(1)
    print('Backbone boundary holds: imports, public interface and version stamp.')
