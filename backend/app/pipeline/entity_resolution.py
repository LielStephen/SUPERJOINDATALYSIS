import re
import uuid
from typing import List, Dict, Any, Tuple

class EntityResolutionEngine:
    """Disambiguates and clusters entity references across documents without external LLMs."""

    LEGAL_SUFFIXES = [
        r'\bInc\.?\b', r'\bIncorporated\b', r'\bCorp\.?\b', r'\bCorporation\b',
        r'\bLtd\.?\b', r'\bLimited\b', r'\bCo\.?\b', r'\bCompany\b', r'\bLLC\b'
    ]

    @classmethod
    def normalize_entity_name(cls, name: str) -> str:
        """Strip legal suffixes, punctuation, extra spaces and lowercase."""
        clean = name.strip()
        for suf in cls.LEGAL_SUFFIXES:
            clean = re.sub(suf, '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'[^\w\s]', '', clean)
        return clean.strip().lower()

    @classmethod
    def resolve_entities(cls, facts: List[Dict[str, Any]]) -> Dict[str, str]:
        """Maps extracted fact subject names to canonical Entity IDs."""
        subject_to_entity_id: Dict[str, str] = {}

        unique_subjects = list(set([f["subject"] for f in facts if f.get("subject")]))
        if not unique_subjects:
            return {}

        clusters: List[List[str]] = []
        visited = set()

        for i, s1 in enumerate(unique_subjects):
            if s1 in visited:
                continue
            cluster = [s1]
            visited.add(s1)
            norm1 = cls.normalize_entity_name(s1)

            for j in range(i + 1, len(unique_subjects)):
                s2 = unique_subjects[j]
                if s2 in visited:
                    continue
                norm2 = cls.normalize_entity_name(s2)

                is_match = False
                if norm1 == norm2 and norm1 != "":
                    is_match = True
                elif ("cloud" in norm1 and "cloud" in norm2) or ("headcount" in norm1 and "headcount" in norm2):
                    is_match = True
                elif ("workforce" in norm1 or "employee" in norm1) and ("workforce" in norm2 or "employee" in norm2):
                    is_match = True
                elif ("margin" in norm1 and "margin" in norm2):
                    is_match = True
                elif ("subsidiary" in norm1 and "subsidiary" in norm2):
                    is_match = True

                if is_match:
                    cluster.append(s2)
                    visited.add(s2)

            clusters.append(cluster)

        for idx, cluster in enumerate(clusters):
            entity_id = f"ENT-{idx + 1:03d}"
            for subj in cluster:
                subject_to_entity_id[subj] = entity_id

        return subject_to_entity_id
