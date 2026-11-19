"""Vista previa de evidencias.

Los formatos que el navegador no puede mostrar (Word, Excel, PowerPoint) se
convierten a PDF al momento de subirlos, para que el investigador pueda
visualizarlos dentro del panel sin descargar el archivo original.
"""
import os
import shutil
import subprocess
import tempfile
import uuid

from django.core.files.base import ContentFile

# Formatos de oficina que se convierten a PDF con LibreOffice.
OFFICE_EXTENSIONS = {
    '.doc', '.docx', '.docm', '.dot', '.dotx',
    '.xls', '.xlsx', '.xlsm', '.xlt', '.xltx',
    '.ppt', '.pptx', '.pptm', '.pot', '.potx',
    '.odt', '.ods', '.odp', '.rtf',
}

VIEWABLE_KINDS = {
    'pdf': {'.pdf'},
    'image': {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'},
    'video': {'.mp4', '.webm', '.ogv', '.mov'},
    'audio': {'.mp3', '.wav', '.ogg', '.oga', '.m4a'},
    'text': {'.txt', '.csv', '.log', '.md', '.json'},
}

CONVERSION_TIMEOUT = 120


def file_extension(name):
    return os.path.splitext(name or '')[1].lower()


def is_office_document(name):
    return file_extension(name) in OFFICE_EXTENSIONS


def viewer_kind(name):
    """Tipo de visor para un archivo, o 'none' si no se puede previsualizar."""
    ext = file_extension(name)
    for kind, extensions in VIEWABLE_KINDS.items():
        if ext in extensions:
            return kind
    return 'none'


def _soffice_binary():
    return shutil.which('soffice') or shutil.which('libreoffice')


def convert_office_to_pdf(field_file):
    """Convierte un documento de oficina a PDF. Devuelve ContentFile o None."""
    binary = _soffice_binary()
    if not binary or not field_file:
        return None

    workdir = tempfile.mkdtemp(prefix='evidence_pdf_')
    try:
        source_name = os.path.basename(field_file.name) or 'documento'
        source_path = os.path.join(workdir, source_name)
        field_file.seek(0)
        with open(source_path, 'wb') as handle:
            for chunk in field_file.chunks():
                handle.write(chunk)

        profile = os.path.join(workdir, 'profile')
        result = subprocess.run(
            [
                binary,
                '--headless',
                '--norestore',
                '--nolockcheck',
                f'-env:UserInstallation=file://{profile}',
                '--convert-to', 'pdf',
                '--outdir', workdir,
                source_path,
            ],
            capture_output=True,
            timeout=CONVERSION_TIMEOUT,
        )
        pdf_path = os.path.join(workdir, f'{os.path.splitext(source_name)[0]}.pdf')
        if result.returncode != 0 or not os.path.exists(pdf_path):
            return None
        with open(pdf_path, 'rb') as handle:
            return ContentFile(handle.read(), name=f'{uuid.uuid4().hex}.pdf')
    except Exception:
        return None
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def build_preview(evidence):
    """Genera y guarda la vista previa PDF de una evidencia, si aplica."""
    if not evidence or not evidence.file:
        return False
    if not is_office_document(evidence.file.name):
        return False
    pdf = convert_office_to_pdf(evidence.file)
    if not pdf:
        return False
    if evidence.preview_pdf:
        evidence.preview_pdf.delete(save=False)
    evidence.preview_pdf.save(pdf.name, pdf, save=True)
    return True
