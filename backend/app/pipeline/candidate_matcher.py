from typing import List, Dict, Any, Tuple
from collections import defaultdict

class CandidateFactMatcher:
    """Retrieves high-probability candidate fact pairs for cross-document reconciliation."""

    @classmethod
    def get_candidate_pairs(cls, facts: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """Group facts by predicate / metric category and return valid cross-document candidate pairs."""
        candidate_pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
        seen_pair_keys = set()

        predicate_buckets = defaultdict(list)

        for fact in facts:
            pred_key = cls._get_predicate_key(fact["predicate"], fact["fact_type"], fact["raw_value"])
            predicate_buckets[pred_key].append(fact)

        for pred_key, bucket_facts in predicate_buckets.items():
            for i in range(len(bucket_facts)):
                for j in range(i + 1, len(bucket_facts)):
                    fact_a = bucket_facts[i]
                    fact_b = bucket_facts[j]

                    if fact_a["id"] == fact_b["id"]:
                        continue

                    # Must come from different documents
                    if fact_a.get("document_id") == fact_b.get("document_id"):
                        continue

                    pair_key = tuple(sorted([fact_a["id"], fact_b["id"]]))
                    if pair_key in seen_pair_keys:
                        continue

                    seen_pair_keys.add(pair_key)
                    candidate_pairs.append((fact_a, fact_b))

        return candidate_pairs

    @classmethod
    def _get_predicate_key(cls, predicate: str, fact_type: str, raw_value: str) -> str:
        """Normalize predicate string into a metric category bucket key."""
        p_clean = predicate.lower().strip()
        r_clean = raw_value.lower().strip()
        
        if "operating margin" in p_clean or "margin" in p_clean or ("%" in r_clean and "margin" in p_clean):
            return "METRIC_OPERATING_MARGIN"
        elif "revenue" in p_clean or "cloud" in p_clean or "billion" in r_clean:
            return "METRIC_REVENUE"
        elif "headcount" in p_clean or "employee" in p_clean or "workforce" in p_clean:
            return "METRIC_HEADCOUNT"
        elif "capital" in p_clean or "capex" in p_clean or "deployment" in p_clean:
            return "METRIC_CAPEX"
        elif "growth" in p_clean or "expansion" in p_clean:
            return "METRIC_GROWTH"
        else:
            return f"GENERIC_{fact_type}"
