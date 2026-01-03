import io
from PIL import Image

def compress_image(img, quality=60):
    
    buffer = io.BytesIO()

    if img.mode != "RGB":
        img = img.convert("RGB")

    img.save(buffer, format="JPEG", quality=quality)
    return buffer.getvalue()
