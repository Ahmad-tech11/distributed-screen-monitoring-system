from PIL import Image
import io

def decode_image(image_bytes):
    
    img = Image.open(io.BytesIO(image_bytes))
    img.load()  
    return img
