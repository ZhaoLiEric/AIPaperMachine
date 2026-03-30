from dataclasses import dataclass, field
from typing import Dict, List


TOP_CONFERENCES: Dict[str, List[str]] = {
    "llm": ["NeurIPS", "ICML", "ICLR", "ACL", "EMNLP", "NAACL"],
    "nlp": ["ACL", "EMNLP", "NAACL", "COLING", "EACL"],
    "cv": ["CVPR", "ICCV", "ECCV", "NeurIPS"],
    "ml": ["NeurIPS", "ICML", "ICLR", "KDD", "AAAI", "IJCAI"],
    "security": ["IEEE S&P", "USENIX Security", "CCS", "NDSS"],
    "systems": ["OSDI", "SOSP", "NSDI", "USENIX ATC"],
}


@dataclass
class AgentConfig:
    domain: str
    keywords: str
    years_back: int = 3
    per_conference_limit: int = 25
    max_papers_in_report: int = 20
    language: str = "zh"
    conferences: List[str] = field(default_factory=list)

    def resolve_conferences(self) -> List[str]:
        if self.conferences:
            return self.conferences
        return TOP_CONFERENCES.get(self.domain.lower(), TOP_CONFERENCES["ml"])
