import re
from typing import Dict, Any, List
import dateparser
from decimal import Decimal

class FactNormalizer:

    MULTIPLIERS = {
        'k': 1_000.0,
        'thousand': 1_000.0,
        'm': 1_000_000.0,
        'mn': 1_000_000.0,
        'million': 1_000_000.0,
        'b': 1_000_000_000.0,
        'bn': 1_000_000_000.0,
        'billion': 1_000_000_000.0,
        't': 1_000_000_000_000.0,
        'trillion': 1_000_000_000_000.0,
        'cr': 10_000_000.0,
        'crore': 10_000_000.0,
        'lakh': 100_000.0,
    }

    CURRENCY_SYMBOLS = {
        '$': 'USD',
        'USD': 'USD',
        'US$': 'USD',
        '€': 'EUR',
        'EUR': 'EUR',
        '£': 'GBP',
        'GBP': 'GBP',
        '₹': 'INR',
        'INR': 'INR',
        'dollars': 'USD',
        'dollar': 'USD'
    }

    @classmethod
    def normalize_number_and_unit(cls, text_val: str) -> Dict[str, Any]:
        text_clean = text_val.strip().replace(',', '')

        result = {
            "raw": text_val,
            "normalized_value": None,
            "normalized_str": None,
            "unit": None,
            "currency": None,
            "fact_type": "NUMERICAL"
        }

        curr_found = None
        for sym, code in cls.CURRENCY_SYMBOLS.items():
            if sym.lower() in text_clean.lower():
                curr_found = code
                break

        if '%' in text_clean or 'percent' in text_clean.lower():
            result["fact_type"] = "PERCENTAGE"
            result["unit"] = "%"
            m = re.search(r'([\d.]+)', text_clean)
            if m:
                try:
                    val = float(m.group(1))
                    result["normalized_value"] = val
                    result["normalized_str"] = f"{val}%"
                    return result
                except ValueError:
                    pass

        match = re.search(r'([\d.]+)\s*(billion|million|thousand|trillion|crore|lakh|b|m|k|mn|bn)?', text_clean, re.IGNORECASE)

        if match:
            num_part = match.group(1)
            mult_part = match.group(2)
            try:
                base_num = float(num_part)
                mult = 1.0
                unit_str = None

                if mult_part:
                    mult_key = mult_part.lower()
                    if mult_key in cls.MULTIPLIERS:
                        mult = cls.MULTIPLIERS[mult_key]
                        unit_str = mult_key

                final_val = base_num * mult
                result["normalized_value"] = final_val

                if curr_found:
                    result["currency"] = curr_found
                    result["fact_type"] = "CURRENCY"
                    result["normalized_str"] = f"{final_val:,.2f} {curr_found}".rstrip('0').rstrip('.')
                else:
                    result["normalized_str"] = f"{final_val:,.2f}".rstrip('0').rstrip('.')
                    if unit_str:
                        result["unit"] = unit_str

            except ValueError:
                pass

        return result

    @classmethod
    def extract_temporal_context(cls, text: str, page_context: str = "") -> Dict[str, Any]:
        result = {
            "temporal_type": None,
            "temporal_year": None,
            "temporal_quarter": None,
            "temporal_period": None,
            "is_relative": False
        }

        full_search = f"{text} {page_context}"

        date_match = re.search(r'\b(?:as\s+of\s+)?(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(20\d{2})\b', full_search, re.IGNORECASE)
        if date_match:
            month_str, day_str, year_str = date_match.groups()
            result["temporal_type"] = "EXACT_DATE"
            result["temporal_year"] = int(year_str)
            result["temporal_period"] = f"{month_str} {day_str}, {year_str}"
            return result

        q_match = re.search(r'\b(?:Q([1-4])|(fourth|third|second|first|[1-4])(?:st|nd|rd|th)?\s+quarter)\s*(?:of\s*)?(?:FY|fiscal\s+year)?\s*(20\d{2})?\b', full_search, re.IGNORECASE)
        if q_match:
            q_str = q_match.group(1) or q_match.group(2)
            q_map = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4, '1': 1, '2': 2, '3': 3, '4': 4}
            q_num = q_map.get(q_str.lower(), 4) if q_str else 4
            year_str = q_match.group(3) or "2023"

            result["temporal_type"] = "QUARTER"
            result["temporal_quarter"] = q_num
            result["temporal_year"] = int(year_str)
            result["temporal_period"] = f"Q{q_num} {year_str}"
            return result

        fy_match = re.search(r'\b(?:FY|fiscal\s+year)\s*\(?20?(\d{2})\)?\b', full_search, re.IGNORECASE)
        if fy_match:
            year_short = fy_match.group(1)
            full_year = int(f"20{year_short}") if len(year_short) == 2 else int(year_short)
            result["temporal_type"] = "FISCAL_YEAR"
            result["temporal_year"] = full_year
            result["temporal_period"] = f"FY{full_year}"
            return result

        rel_match = re.search(r'\b(coming\s+cycle|next\s+period|future\s+cycle|coming\s+year)\b', full_search, re.IGNORECASE)
        if rel_match:
            result["temporal_type"] = "RELATIVE"
            result["temporal_period"] = rel_match.group(1).lower()
            result["is_relative"] = True
            return result

        return result

    @classmethod
    def extract_scope_qualifiers(cls, text: str) -> List[str]:
        qualifiers = []
        text_upper = text.upper()

        keywords = {
            "GAAP": ["GAAP"],
            "Non-GAAP": ["NON-GAAP", "ADJUSTED NON-GAAP", "ADJUSTED"],
            "Consolidated": ["CONSOLIDATED"],
            "Subsidiary": ["SUBSIDIARY", "REGIONAL SUBSIDIARY"],
            "Full-time": ["FULL-TIME", "PERMANENT FULL-TIME"],
            "Active permanent": ["ACTIVE PERMANENT", "PERMANENT EMPLOYEES"],
            "Cloud Infrastructure": ["CLOUD INFRASTRUCTURE", "CLOUD BUSINESS"],
            "Core Software": ["CORE SOFTWARE"],
        }

        for key, patterns in keywords.items():
            for pat in patterns:
                if pat in text_upper:
                    qualifiers.append(key)
                    break

        return qualifiers
