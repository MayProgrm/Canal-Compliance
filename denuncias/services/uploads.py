import os

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_complaint_upload(uploaded_file):
    max_size = int(settings.MAX_UPLOAD_SIZE)
    if uploaded_file.size > max_size:
        raise ValidationError(
            f'El archivo es demasiado grande. Máximo: {max_size // (1024 * 1024)}MB.'
        )

    extension = os.path.splitext(uploaded_file.name)[1].lower()
    allowed_extensions = set(settings.ALLOWED_UPLOAD_EXTENSIONS)
    if extension not in allowed_extensions:
        raise ValidationError('Tipo de archivo no permitido.')

    try:
        header = uploaded_file.read(16)
        uploaded_file.seek(0)
    except (AttributeError, OSError, ValueError):
        raise ValidationError('No se pudo validar el contenido del archivo.')

    starts_with = header.startswith
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    office_zip_extensions = {'.docx', '.xlsx', '.pptx'}
    is_pdf = starts_with(b'%PDF')
    is_png = starts_with(b'\x89PNG\r\n\x1a\n')
    is_jpg = starts_with(b'\xff\xd8')
    is_gif = starts_with(b'GIF87a') or starts_with(b'GIF89a')
    is_webp = starts_with(b'RIFF') and len(header) >= 12 and header[8:12] == b'WEBP'
    is_zip = starts_with(b'PK\x03\x04') or starts_with(b'PK\x05\x06')
    is_doc = starts_with(b'\xd0\xcf\x11\xe0')

    if extension == '.pdf' and not is_pdf:
        raise ValidationError('El contenido no coincide con un PDF válido.')
    if extension in image_extensions and not (is_png or is_jpg or is_gif or is_webp):
        raise ValidationError('El contenido no coincide con una imagen válida.')
    if extension in office_zip_extensions and not is_zip:
        raise ValidationError('El contenido no coincide con un archivo Office válido.')
    if extension == '.doc' and not is_doc:
        raise ValidationError('El contenido no coincide con un archivo .doc válido.')
