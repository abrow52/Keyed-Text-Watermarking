# connecting the detector to the service

from .detector import detect
from .detector import key as watermarkKey


def detectorConnection(threshold=0.65, key=None):
    activeKey = (watermarkKey if key is None else key)

    def serverDetector(text):
        return detect(text, activeKey, threshold,)

    return serverDetector
