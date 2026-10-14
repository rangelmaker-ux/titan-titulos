"""Titan Titles Studio: public GitHub Releases, verified packages and rollback."""
import ast
import base64
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import shutil
import ssl
import sys
import tempfile
import threading
import time
import urllib.request
from urllib.parse import urlsplit
import zipfile
import zlib

REPO = 'rangelmaker-ux/titan-titulos'
API = 'https://api.github.com/repos/' + REPO + '/releases/latest'
ASSET = 'Titan-Titles-Studio-Update.zip'
MAX_BYTES = 32 * 1024 * 1024

def version(value):
    match = re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)', str(value))
    if not match:
        raise ValueError('Versão de atualização inválida.')
    return tuple(map(int, match.groups()))

def allowed_url(url):
    p = urlsplit(url)
    hosts = {'api.github.com', 'github.com', 'release-assets.githubusercontent.com', 'objects.githubusercontent.com'}
    if p.scheme != 'https' or p.hostname not in hosts or p.username or p.password or p.port not in (None, 443):
        raise ValueError('Endereço de atualização inválido.')
    if p.hostname == 'api.github.com' and not p.path.startswith('/repos/' + REPO + '/'):
        raise ValueError('Repositório de atualização inválido.')
    if p.hostname == 'github.com' and not p.path.startswith('/' + REPO + '/releases/'):
        raise ValueError('Repositório de atualização inválido.')
    return url

def open_url(url):
    class Redirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            allowed_url(newurl)
            return super().redirect_request(req, fp, code, msg, headers, newurl)
    context = ssl.create_default_context()
    try:
        import certifi
        context.load_verify_locations(certifi.where())
    except ImportError:
        pass
    opener = urllib.request.build_opener(Redirect(), urllib.request.HTTPSHandler(context=context))
    return opener.open(urllib.request.Request(allowed_url(url), headers={
        'User-Agent': 'Titan-Titles-Studio-Updater', 'Accept': 'application/vnd.github+json'}), timeout=10)

def check_status(current):
    """Return an explicit updater state for manual checks and clear UI feedback."""
    try:
        with open_url(API) as response:
            raw = response.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            return ('error', None)
        release = json.loads(raw)
        tag = release.get('tag_name', '')
        if release.get('draft') or release.get('prerelease'):
            return ('error', None)
        if version(tag) <= version(current):
            return ('current', None)
        assets = {a['name']: a for a in release.get('assets', [])}
        asset = assets.get(ASSET)
        if not asset or not re.fullmatch(r'sha256:[0-9a-f]{64}', asset.get('digest') or ''):
            return ('unavailable', None)
        info = (tag, {'url': allowed_url(asset['browser_download_url']),
                      'sha256': asset['digest'][7:], 'version': tag}, 'Atualização pelo GitHub')
        return ('available', info)
    except Exception:
        return ('error', None)

def check(current):
    """Backward-compatible silent check used when the plugin starts."""
    status, info = check_status(current)
    return info if status == 'available' else None

def validate_package(path, expected_version):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or sum(i.file_size for i in archive.infolist()) > MAX_BYTES:
            raise ValueError('Pacote inválido ou muito grande.')
        manifest = json.loads(archive.read('manifest.json'))
        if manifest.get('product') != 'Titan Titles Studio' or manifest.get('version') != expected_version:
            raise ValueError('Este pacote não corresponde à atualização.')
        files = manifest.get('files', {})
        if not isinstance(files, dict) or not files or set(names) != set(files) | {'manifest.json'}:
            raise ValueError('Conteúdo do pacote inválido.')
        if not {'Titan Titles Studio.py', 'titan_update.py'} <= set(files):
            raise ValueError('Pacote incompleto.')
        data = {}
        for name, digest in files.items():
            if name not in ('Titan Titles Studio.py', 'titan_update.py', 'titan_locale.py', 'titan_sfx.py', 'sfx/manifest.json') and not re.fullmatch(r'(?:icons/[A-Za-z0-9_-]+\.(?:png|jpg)|sfx/[A-Za-z0-9_-]+\.wav)', name):
                raise ValueError('Arquivo não permitido na atualização.')
            content = archive.read(name)
            if hashlib.sha256(content).hexdigest() != digest:
                raise ValueError('Falha de integridade no pacote.')
            if name.endswith('.py'):
                ast.parse(content.decode('utf-8'))
            data[name] = content
        data.update(read_resource_bundle(data['titan_update.py']))
        if not {'titan_locale.py','titan_sfx.py','sfx/whoosh.wav','sfx/glitch.wav','sfx/motionblur.wav'} <= set(data):
            raise ValueError('Pacote de recursos incompleto.')
        return data

def read_resource_bundle(source):
    """Read data literals without executing downloaded code. Legacy updaters
    accept only the original file list; their new updater contains the resources."""
    tree=ast.parse(source.decode('utf-8'))
    value=next((n.value for n in tree.body if isinstance(n,ast.Assign) and
                any(isinstance(t,ast.Name) and t.id=='_TITAN_BUNDLE' for t in n.targets)),None)
    if value is None:return {}
    packed=base64.b64decode(ast.literal_eval(value),validate=True)
    raw=zlib.decompressobj().decompress(packed,MAX_BYTES+1)
    if len(raw)>MAX_BYTES:raise ValueError('Recursos excedem o limite.')
    bundle=json.loads(raw)
    result={}
    for name,info in bundle.items():
        if name not in ('titan_locale.py','titan_sfx.py','sfx/manifest.json') and not re.fullmatch(r'sfx/[A-Za-z0-9_-]+\.wav',name):
            raise ValueError('Recurso de atualização inválido.')
        content=base64.b64decode(info['data'],validate=True)
        if hashlib.sha256(content).hexdigest()!=info['sha256']:raise ValueError('Recurso alterado.')
        if name.endswith('.py'):ast.parse(content.decode('utf-8'))
        result[name]=content
    return result

def retire_legacy(root,backup):
    for name in ('Titan Titles Studio.py', 'Titan Titulo Studio.py',
                 'Titan Titles Studio Backup.py', 'Titan Titulo Studio Backup.py',
                 'Titan Update.py', 'titan_update.py', 'titan_locale.py', 'titan_sfx.py', 'TitanTitlesStudio', 'TitanTitlesStudio-backups'):
        legacy = root / name
        if not legacy.exists():continue
        if legacy.is_symlink() or (hasattr(legacy, 'is_junction') and legacy.is_junction()):
            raise ValueError('Arquivo antigo redirecionado; limpeza interrompida.')
        saved=backup/('legacy-'+name)
        if legacy.is_dir():
            with zipfile.ZipFile(str(saved)+'.zip','w',zipfile.ZIP_DEFLATED) as archive:
                for file in legacy.rglob('*'):
                    if file.is_file():archive.write(file,str(file.relative_to(legacy)))
            for script in legacy.rglob('*'):
                if script.is_file() and script.suffix.lower() in ('.py','.lua'):script.unlink()
            try:shutil.rmtree(legacy)
            except OSError:
                if any(p.suffix.lower() in ('.py','.lua') for p in legacy.rglob('*') if p.is_file()):raise
        else:shutil.move(str(legacy),str(saved))

def install_package(path, expected_version, install_root):
    data = validate_package(path, expected_version)
    root = Path(install_root).absolute()
    if not root.is_dir() or any(p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()) for p in (root, *root.parents)):
        raise ValueError('Pasta de instalação inválida.')
    # Canonicalize Windows 8.3 names without confusing them with redirects.
    root = root.resolve()
    fusion_root = root.parent.parent
    resources = fusion_root / 'TitanTitlesStudio'
    targets = {name: root / 'Titan Studio.py' if name == 'Titan Titles Studio.py' else resources / name for name in data}
    for target in targets.values():
        if target.resolve() != target.absolute():
            raise ValueError('Arquivo redirecionado; reinstale o plugin.')
    backup_parent = fusion_root / 'TitanTitlesStudio-backups'
    if backup_parent.is_symlink():
        raise ValueError('Pasta de backup inválida.')
    backup = backup_parent / (time.strftime('%Y%m%d-%H%M%S') + '-' + str(time.time_ns()))
    backup.mkdir(parents=True)
    old, written = {}, []
    try:
        for name, target in targets.items():
            old[name] = target.read_bytes() if target.exists() else None
            if old[name] is not None:
                saved = backup / name
                saved.parent.mkdir(parents=True, exist_ok=True)
                saved.write_bytes(old[name])
        # Replace the entry script last; downloaded bytes are fully verified first.
        for name in sorted(data, key=lambda n: n == 'Titan Titles Studio.py'):
            target = targets[name]
            target.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(prefix='.titan-', dir=str(target.parent))
            try:
                with os.fdopen(fd, 'wb') as output:
                    output.write(data[name]); output.flush(); os.fsync(output.fileno())
                os.replace(temporary, target)
                written.append(name)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
    except Exception:
        for name in reversed(written):
            if old[name] is None:
                targets[name].unlink()
            else:
                targets[name].write_bytes(old[name])
        raise
    retire_legacy(root,backup)
    return str(backup)

class Atualizador:
    def __init__(self, install_root):
        self.install_root = install_root
        self.eventos = queue.Queue()
        self.ocupado = False
        self.arquivo = None
        self.release = None
    def iniciar(self, release):
        if self.ocupado or self.arquivo:
            return False
        self.ocupado = True
        self.release = release
        def worker():
            folder = tempfile.mkdtemp(prefix='titan-update-')
            path = os.path.join(folder, ASSET)
            try:
                with open_url(release['url']) as response, open(path, 'wb') as output:
                    total = int(response.headers.get('Content-Length') or 0)
                    count = 0
                    digest = hashlib.sha256()
                    while True:
                        chunk = response.read(256 * 1024)
                        if not chunk:
                            break
                        count += len(chunk)
                        if count > MAX_BYTES:
                            raise ValueError('Pacote excede o limite de tamanho.')
                        digest.update(chunk); output.write(chunk)
                        self.eventos.put(('progresso', count, total))
                if (total and count != total) or digest.hexdigest() != release['sha256']:
                    raise ValueError('Download incompleto ou inválido.')
                validate_package(path, release['version'])
                self.arquivo = path
                self.eventos.put(('pronto', path))
            except Exception:
                shutil.rmtree(folder, ignore_errors=True)
                self.eventos.put(('erro', 'Não foi possível baixar. Confira a conexão e tente novamente.'))
            finally:
                self.ocupado = False
        threading.Thread(target=worker, daemon=True).start()
        return True
    def instalar(self):
        if not self.arquivo or not self.release:
            raise ValueError('Baixe a atualização primeiro.')
        # Recheck the complete downloaded ZIP before writing files.
        if hashlib.sha256(Path(self.arquivo).read_bytes()).hexdigest() != self.release['sha256']:
            raise ValueError('Pacote de atualização alterado.')
        backup = install_package(self.arquivo, self.release['version'], self.install_root)
        shutil.rmtree(os.path.dirname(self.arquivo), ignore_errors=True)
        self.arquivo = None
        return backup
