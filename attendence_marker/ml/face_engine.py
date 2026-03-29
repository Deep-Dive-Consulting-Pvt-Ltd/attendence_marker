import cv2
import numpy as np
from insightface.app import FaceAnalysis

from core.logging import get_logger
from utils import l2_normalize

logger = get_logger(__name__)

_face_app: FaceAnalysis | None = None


def get_face_app() -> FaceAnalysis:
    global _face_app
    if _face_app is None:
        logger.info("loading_face_model")
        _face_app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        _face_app.prepare(ctx_id=0, det_size=(640, 640))
        logger.info("face_model_ready")
    return _face_app


def extract_embedding(image_path: str):
    img = cv2.imread(image_path)
    if img is None:
        return None
    faces = get_face_app().get(img)
    if not faces:
        return None
    face = max(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]))
    return l2_normalize(np.array(face.embedding, dtype=np.float32))
