from abc import ABC, abstractmethod

from src.evidence_pack import EvidencePack
from src.models import LeadProfileDraft


class LLMExtractor(ABC):

    @abstractmethod
    def extract(self, evidence: EvidencePack) -> LeadProfileDraft:
        pass