import numpy as np
import open_clip
import torch
from PIL import Image

from labellens.config import settings


class ClipImageEmbedder:
    """OpenCLIP: images and text live in the SAME vector space (512-d for ViT-B/32)."""

    def __init__(self, model_name: str | None = None, pretrained: str | None = None)-> None:
        self.model_name = model_name or settings.image_embed_model
        pretrained = pretrained or settings.image_embed_pretrained
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.half = self.device == "cuda"

        model, _, self.preprocess = open_clip.create_model_and_transforms(
            self.model_name, pretrained=pretrained
        )
        self.model = model.to(self.device).eval()
        if self.half:
            self.model = self.model.half()
        self.tokenizer = open_clip.get_tokenizer(self.model_name)
        self.dim = 512

    @torch.no_grad()
    def embed_images(self, images: list[Image.Image]) -> np.ndarray:
        batch = torch.stack([self.preprocess(im.convert("RGB")) for im in images]).to(self.device)
        if self.half:
            batch = batch.half()
        feats = self.model.encode_image(batch)
        feats = feats / feats.norm(dim=-1, keepdim=True)
        return feats.float().cpu().numpy()

    @torch.no_grad()
    def embed_text(self, text: str) -> np.ndarray:
        tokens = self.tokenizer([text]).to(self.device)
        feats = self.model.encode_text(tokens)
        feats = feats / feats.norm(dim=-1, keepdim=True)
        return feats.float().cpu().numpy()[0]