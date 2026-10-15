import numpy as np
from PIL import Image


class EasyOcr:
    def __init__(self) -> None:
        import easyocr
        import torch

        self.reader = easyocr.Reader(["en"], gpu=torch.cuda.is_available())

    def read(self, image: Image.Image) -> list[str]:
        return [str(text) for text in self.reader.readtext(np.array(image), detail=0)]
