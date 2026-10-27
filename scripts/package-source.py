"""Package reproducible source, excluding credentials, runtimes and generated data."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parents[1]
output = root / 'Nubixia-codigo-fuente.zip'
excluded = {'node_modules', 'target', 'dist', 'data', '.git', '.angular', '.aws-sam', '.tools', '.github', '__pycache__'}
runtime_config = 'comprobastes-serverless-frontend/public/config.json'
with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
    for source in root.rglob('*'):
        relative = source.relative_to(root)
        if any(part in excluded for part in relative.parts) or not source.is_file():
            continue
        if source.suffix in {'.zip', '.log', '.pid'}:
            continue
        if source.name.startswith('.env') and source.name != '.env.example':
            continue
        if relative.as_posix() == runtime_config:
            archive.writestr(runtime_config, '{"apiUrl":"http://localhost:8080","autoConnectLocal":true}\n')
        else:
            archive.write(source, relative.as_posix())
with ZipFile(output) as archive:
    assert not any('.env.aws' in name or '/node_modules/' in name for name in archive.namelist())
    print(f'{output.name}: {len(archive.namelist())} archivos, {output.stat().st_size} bytes; sin claves privadas.')
