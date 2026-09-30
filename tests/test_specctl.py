import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'kit/specctl.py'
spec = importlib.util.spec_from_file_location('specctl', CLI)
specctl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(specctl)


def snapshot(path):
    return {p.relative_to(path).as_posix(): p.read_bytes() for p in path.rglob('*') if p.is_file()}


class StarterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'project'
        self.root.mkdir()

    def cli(self, *args, success=True, source=CLI):
        result = subprocess.run([sys.executable, str(source), *args, '--target', str(self.root)], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0 if success else 1, result.stdout + result.stderr)
        return result

    def install(self, *args):
        return self.cli('install', '--apply', *args)

    def feature(self):
        self.install()
        self.cli('new', '001-demo', '--apply')
        return self.root / 'specs/001-demo'

    def load_spec(self, directory):
        return json.loads((directory / 'spec.json').read_text())

    def save_spec(self, directory, data):
        (directory / 'spec.json').write_text(json.dumps(data))

    def complete(self, directory):
        for path in directory.glob('*.md'):
            path.write_text('Decisión revisada, sin preguntas pendientes.\n')
        data = self.load_spec(directory)
        data['title'] = 'Resultado'
        data['requirements'][0]['statement'] = 'El resultado es estable'
        data['acceptance'][0].update(given='Contexto', when='Acción', then='Resultado', test_refs=[{'path':'test_demo.py','assertion':'resultado esperado'}])
        data['tasks'][0]['title'] = 'Implementar resultado'
        (self.root / 'test_demo.py').write_text('assert True\n')
        self.save_spec(directory, data)
        return data

    def test_dry_run_writes_nothing(self):
        before = snapshot(self.root)
        self.cli('install', '--github')
        self.assertEqual(snapshot(self.root), before)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_install_idempotent(self):
        self.install()
        before = snapshot(self.root)
        result = self.install()
        self.assertIn('0 archivos', result.stdout)
        self.assertEqual(snapshot(self.root), before)

    def test_collision_blocks_all_writes(self):
        (self.root / '.github').mkdir()
        (self.root / '.github/pull_request_template.md').write_text('user content')
        before = snapshot(self.root)
        self.cli('install', '--github', '--apply', success=False)
        self.assertEqual(snapshot(self.root), before)
        self.assertFalse((self.root / '.specify').exists())

    def test_identical_unowned_files_still_collide(self):
        (self.root / '.specify').mkdir()
        shutil.copy(CLI, self.root / '.specify/specctl.py')
        self.cli('install', '--apply', success=False)
        self.assertFalse((self.root / '.specify/manifest.json').exists())

    def test_config_preserved_and_adapter_is_informational(self):
        self.install('--adapter', 'laravel')
        config = self.root / '.specify/project.json'
        data = json.loads(config.read_text())
        data['commands']['test'] = ['echo', 'custom']
        config.write_text(json.dumps(data))
        before = config.read_bytes()
        self.cli('update', '--apply')
        self.assertEqual(config.read_bytes(), before)
        self.assertIn('custom', self.cli('commands').stdout)

    def test_github_opt_in_and_managed(self):
        self.install('--github')
        self.assertTrue((self.root / '.github/workflows/spec-validation.yml').exists())
        self.assertFalse((self.root / 'AGENTS.md').exists())
        self.cli('update', '--apply')

    def test_github_expansion_rejected_on_update(self):
        self.install()
        self.cli('update', '--github', '--apply', success=False)
        self.assertFalse((self.root / '.github').exists())

    def test_local_edits_block_update_without_mutation(self):
        self.install()
        (self.root / '.specify/templates/spec.md').write_text('edited')
        before = snapshot(self.root)
        self.cli('update', '--apply', success=False)
        self.assertEqual(snapshot(self.root), before)

    def test_missing_managed_file_blocks_update(self):
        self.install()
        (self.root / '.specify/templates/spec.md').unlink()
        self.cli('update', success=False)

    def test_update_requires_install(self):
        self.cli('update', success=False)

    def test_stale_manifest_rejected(self):
        self.install()
        path = self.root / '.specify/manifest.json'
        data = json.loads(path.read_text())
        data['release_sha256'] = '0'*64
        path.write_text(json.dumps(data))
        self.cli('update', success=False)

    def test_manifest_traversal_rejected(self):
        self.install()
        path = self.root / '.specify/manifest.json'
        data = json.loads(path.read_text())
        data['files']['../outside'] = '0'*64
        path.write_text(json.dumps(data))
        self.cli('update', success=False)

    def test_install_lock_blocks_apply_but_dry_run_remains_read_only(self):
        (self.root / '.specify-install.lock').write_text('active')
        self.cli('install')
        self.cli('install', '--apply', success=False)
        self.assertEqual((self.root / '.specify-install.lock').read_text(), 'active')

    def test_release_tamper_rejected(self):
        bundle = Path(self.temp.name) / 'bundle'
        shutil.copytree(ROOT / 'kit', bundle)
        (bundle / 'templates/spec.md').write_text('tamper')
        self.cli('install', '--apply', source=bundle / 'specctl.py', success=False)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_safe_version_upgrade(self):
        self.install()
        bundle = Path(self.temp.name) / 'bundle'
        shutil.copytree(ROOT / 'kit', bundle)
        source = bundle / 'specctl.py'
        source.write_text(source.read_text().replace('VERSION = "0.1.0"','VERSION = "0.1.1"'))
        (bundle / 'templates/spec.md').write_text('Nueva plantilla\n')
        release = json.loads((bundle / 'release.json').read_text())
        release['version'] = '0.1.1'
        release['files'] = {name: hashlib.sha256((bundle / name).read_bytes()).hexdigest() for name in release['files']}
        (bundle / 'release.json').write_bytes(specctl.json_bytes(release))
        before = snapshot(self.root)
        self.cli('update', source=source)
        self.assertEqual(snapshot(self.root), before)
        self.cli('update', '--apply', source=source)
        self.assertEqual((self.root / '.specify/templates/spec.md').read_text(), 'Nueva plantilla\n')
        self.cli('update', success=False)  # old CLI cannot downgrade 0.1.1

    def test_new_feature_dry_run_and_collision(self):
        self.install()
        before = snapshot(self.root)
        self.cli('new', '001-demo')
        self.assertEqual(snapshot(self.root), before)
        self.cli('new', '001-demo', '--apply')
        before = snapshot(self.root)
        self.cli('new', '001-demo', '--apply', success=False)
        self.assertEqual(snapshot(self.root), before)

    def test_path_traversal_and_invalid_slugs(self):
        self.install()
        for slug in ('../escape', '/absolute', 'a/b', 'a\\b', 'UPPER', 'a..b'):
            with self.subTest(slug=slug):
                self.cli('new', slug, '--apply', success=False)

    def test_invalid_specs_dir(self):
        self.install()
        config_path = self.root / '.specify/project.json'
        config = json.loads(config_path.read_text())
        for unsafe in ('../outside', '/tmp', '.git/specs', '.specify/specs', 'a\\b'):
            config['specs_dir'] = unsafe
            config_path.write_text(json.dumps(config))
            self.cli('validate', success=False)

    @unittest.skipUnless(hasattr(os, 'symlink') and os.name != 'nt', 'symlink privileges vary on Windows')
    def test_symlink_target_and_destination_rejected(self):
        outside = Path(self.temp.name) / 'outside'
        outside.mkdir()
        (self.root / '.specify').symlink_to(outside, target_is_directory=True)
        self.cli('install', '--apply', success=False)
        self.assertEqual(list(outside.iterdir()), [])

    @unittest.skipUnless(hasattr(os, 'symlink') and os.name != 'nt', 'symlink privileges vary on Windows')
    def test_symlink_spec_json_rejected(self):
        directory = self.feature()
        spec = directory / 'spec.json'
        outside = Path(self.temp.name) / 'outside.json'
        outside.write_bytes(spec.read_bytes())
        spec.unlink()
        spec.symlink_to(outside)
        self.cli('validate', success=False)

    def test_empty_project_validation(self):
        self.install()
        self.cli('validate')
        self.cli('validate', '--strict', success=False)

    def test_draft_valid_strict_incomplete(self):
        self.feature()
        self.cli('validate')
        self.cli('validate', '--strict', success=False)

    def test_completed_feature_passes_strict(self):
        directory = self.feature()
        self.complete(directory)
        self.cli('validate', '--strict')

    def test_schema_version_requires_integer(self):
        directory = self.feature()
        data = self.load_spec(directory)
        for invalid in (True, 1.0, "1", None):
            data['schema_version'] = invalid
            self.save_spec(directory, data)
            self.cli('validate', success=False)

    def test_reserved_or_control_paths_rejected(self):
        for path in ('CON', 'aux.txt', 'dir/lpt1.md', 'a\x00b', 'line\nbreak'):
            with self.subTest(path=path), self.assertRaises(specctl.SpecError):
                specctl.relative(path)

    def test_unknown_and_duplicate_json_fields_rejected(self):
        directory = self.feature()
        data = self.load_spec(directory)
        data['requirements'][0]['statment'] = 'typo'
        self.save_spec(directory, data)
        self.cli('validate', success=False)
        (directory / 'spec.json').write_text('{"id":"a","id":"b"}')
        self.cli('validate', success=False)

    def test_duplicate_and_dangling_ids(self):
        directory = self.feature()
        original = self.load_spec(directory)
        mutations = []
        data = copy.deepcopy(original); data['requirements'].append(data['requirements'][0]); mutations.append(data)
        data = copy.deepcopy(original); data['acceptance'][0]['requirement_ids']=['R-999']; mutations.append(data)
        data = copy.deepcopy(original); data['tasks'][0]['acceptance_ids']=['AC-999']; mutations.append(data)
        data = copy.deepcopy(original); data['requirements'].append({'id':'R-002','statement':'uncovered'}); mutations.append(data)
        for data in mutations:
            self.save_spec(directory, data)
            self.cli('validate', success=False)

    def test_test_reference_escape_and_missing(self):
        directory = self.feature()
        data = self.complete(directory)
        for path in ('../outside', 'missing.py', '/etc/passwd', '.git/config'):
            data['acceptance'][0]['test_refs'][0]['path'] = path
            self.save_spec(directory, data)
            self.cli('validate', '--strict', success=False)

    def test_implemented_requires_done(self):
        directory = self.feature()
        data = self.complete(directory)
        data['status'] = 'implemented'
        self.save_spec(directory, data)
        self.cli('validate', success=False)
        data['tasks'][0]['status']='done'
        self.save_spec(directory, data)
        self.cli('validate')

    def test_transaction_rolls_back_after_link_failure(self):
        real_link = os.link
        calls = 0
        def fail_second(src, dst):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('simulated disk error')
            return real_link(src, dst)
        with mock.patch.object(specctl.os, 'link', side_effect=fail_second):
            with self.assertRaises(OSError):
                specctl.write_transaction(self.root, {'a/one':(None,b'one'),'a/two':(None,b'two')})
        self.assertEqual(list(self.root.iterdir()), [])

    def test_example_contract_is_complete(self):
        self.install()
        shutil.copytree(ROOT / 'examples/001-export-report', self.root / 'specs/001-export-report')
        shutil.copytree(ROOT / 'examples/code', self.root / 'example-code')
        self.cli('validate', '--strict')


if __name__ == '__main__':
    unittest.main()
