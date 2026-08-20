"""Biological regions inside the one SMI Brain."""

from .amygdala import Amygdala
from .brainstem import Brainstem
from .cerebellum import Cerebellum
from .corpus_callosum import CorpusCallosum
from .frontal_lobe import FrontalLobe
from .hemispheres import LeftHemisphere, RightHemisphere
from .hippocampus import Hippocampus
from .hypothalamus import Hypothalamus
from .occipital_lobe import OccipitalLobe
from .parietal_lobe import ParietalLobe
from .synthetic_mind import SyntheticMind
from .temporal_lobe import TemporalLobe
from .thalamus import Thalamus

__all__ = [
    "Amygdala",
    "Brainstem",
    "Cerebellum",
    "CorpusCallosum",
    "FrontalLobe",
    "Hippocampus",
    "Hypothalamus",
    "LeftHemisphere",
    "OccipitalLobe",
    "ParietalLobe",
    "RightHemisphere",
    "SyntheticMind",
    "TemporalLobe",
    "Thalamus",
]
