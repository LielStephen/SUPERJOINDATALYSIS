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
    def find_candidate_pairs(cls, facts: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """Alias for get_candidate_pairs for compatibility."""
        return cls.get_candidate_pairs(facts)


    @classmethod
    def _get_predicate_key(cls, predicate: str, fact_type: str, raw_value: str) -> str:
        """Normalize predicate string into a metric category bucket key."""
        import re
        p_clean = predicate.lower().strip()
        r_clean = raw_value.lower().strip()
        
        if "margin" in p_clean:
            return "METRIC_OPERATING_MARGIN"
        elif "revenue" in p_clean or "sales" in p_clean or "turnover" in p_clean or "cloud" in p_clean:
            return "METRIC_REVENUE"
        elif "headcount" in p_clean or "employee" in p_clean or "workforce" in p_clean or "staff" in p_clean:
            return "METRIC_HEADCOUNT"
        elif "income" in p_clean or "profit" in p_clean or "loss" in p_clean or "ebit" in p_clean or "earnings" in p_clean:
            return "METRIC_PROFIT_LOSS"
        elif "capital" in p_clean or "capex" in p_clean or "deployment" in p_clean or "investment" in p_clean:
            return "METRIC_CAPEX"
        elif "growth" in p_clean or "expansion" in p_clean or "increase" in p_clean or "decline" in p_clean:
            return "METRIC_GROWTH"
        elif "eps" in p_clean or "per share" in p_clean:
            return "METRIC_EPS"
        elif "debt" in p_clean or "borrowing" in p_clean or "liability" in p_clean:
            return "METRIC_DEBT"
        elif "cash" in p_clean or "liquidity" in p_clean:
            return "METRIC_CASH"
        elif "deliver" in p_clean or "shipment" in p_clean or "production" in p_clean or "volume" in p_clean:
            return "METRIC_VOLUME"
        else:
            words = [w for w in re.findall(r'\b[a-z]{3,}\b', p_clean) if w not in ['the', 'and', 'for', 'was', 'were', 'our', 'with', 'from', 'has', 'reported']]
            if words:
                return f"METRIC_{words[0].upper()}"
            return f"GENERIC_{fact_type}"

