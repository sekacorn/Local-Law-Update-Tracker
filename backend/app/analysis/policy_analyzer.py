"""
Policy Analyzer for Terms of Service, Privacy Policies, and User Agreements
Focuses on data rights, power imbalances, and consumer protections
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PowerImbalance:
    """Represents an identified power imbalance in the agreement"""
    category: str  # e.g., "unilateral_changes", "data_rights", "liability_asymmetry"
    description: str
    severity: str  # "low", "medium", "high"
    company_power: str  # What the company can do
    user_power: str  # What the user can do (often limited)
    citation_text: str
    start_char: int
    end_char: int


@dataclass
class DataRightIssue:
    """Issues related to user data and privacy"""
    right_type: str  # e.g., "collection", "sharing", "retention", "deletion"
    description: str
    user_control: str  # "none", "limited", "full"
    citation_text: str
    start_char: int
    end_char: int


# Power imbalance detection patterns
POWER_IMBALANCE_PATTERNS = {
    "unilateral_changes": {
        "keywords": [
            "reserve the right to modify",
            "may change these terms",
            "update these terms at any time",
            "modify without notice",
            "sole discretion",
            "at our discretion",
            "without prior notice"
        ],
        "severity": "high",
        "description": "Company can change terms unilaterally"
    },
    "liability_asymmetry": {
        "keywords": [
            "not liable for",
            "disclaimer of warranties",
            "AS IS",
            "no warranty",
            "limit our liability",
            "maximum liability",
            "not responsible for",
            "user assumes all risk"
        ],
        "severity": "high",
        "description": "Company limits its liability while user bears risks"
    },
    "forced_arbitration": {
        "keywords": [
            "binding arbitration",
            "waive right to sue",
            "waive right to jury trial",
            "arbitration agreement",
            "class action waiver",
            "individual basis only"
        ],
        "severity": "high",
        "description": "Limits user's legal recourse"
    },
    "account_termination": {
        "keywords": [
            "terminate your account",
            "suspend access at any time",
            "discontinue service",
            "without cause",
            "for any reason",
            "sole discretion to terminate"
        ],
        "severity": "medium",
        "description": "Company can terminate account with minimal recourse"
    },
    "data_usage": {
        "keywords": [
            "use your data",
            "analyze your information",
            "share with third parties",
            "sell your data",
            "transfer your information",
            "for any purpose"
        ],
        "severity": "high",
        "description": "Broad data usage rights for company"
    },
    "ip_transfer": {
        "keywords": [
            "you grant us",
            "transfer all rights",
            "perpetual license",
            "irrevocable license",
            "worldwide license",
            "royalty-free license"
        ],
        "severity": "medium",
        "description": "User grants extensive rights to their content"
    }
}

# Data rights patterns
DATA_RIGHTS_PATTERNS = {
    "collection": {
        "keywords": [
            "we collect",
            "information we gather",
            "data collection",
            "automatically collect",
            "cookies",
            "tracking"
        ],
        "concerns": ["scope", "necessity", "transparency"]
    },
    "sharing": {
        "keywords": [
            "share with",
            "third parties",
            "partners",
            "affiliates",
            "disclose to",
            "provide to others"
        ],
        "concerns": ["who", "why", "control"]
    },
    "retention": {
        "keywords": [
            "retain",
            "store",
            "keep your data",
            "retention period",
            "indefinitely"
        ],
        "concerns": ["duration", "purpose", "deletion"]
    },
    "rights": {
        "keywords": [
            "right to access",
            "right to delete",
            "opt out",
            "data portability",
            "correct",
            "update your information"
        ],
        "concerns": ["access", "control", "limitations"]
    }
}

# Consumer protection red flags
CONSUMER_RED_FLAGS = {
    "hidden_fees": [
        "additional charges",
        "processing fee",
        "service fee",
        "subject to fees",
        "may charge"
    ],
    "auto_renewal": [
        "automatically renew",
        "auto-renew",
        "continuous subscription",
        "unless cancelled"
    ],
    "no_refund": [
        "non-refundable",
        "no refunds",
        "all sales final",
        "cannot be refunded"
    ],
    "broad_indemnity": [
        "you agree to indemnify",
        "hold us harmless",
        "defend and indemnify",
        "reimburse us for"
    ]
}


def detect_power_imbalances(text: str) -> List[PowerImbalance]:
    """
    Detect power imbalances in the policy
    Returns list of identified imbalances with citations
    """
    imbalances = []
    text_lower = text.lower()

    for category, config in POWER_IMBALANCE_PATTERNS.items():
        for keyword in config["keywords"]:
            # Find sentences containing the keyword
            pattern = re.compile(
                r'([^.!?]{0,200}' + re.escape(keyword) + r'[^.!?]{0,200}[.!?])',
                re.IGNORECASE
            )

            for match in pattern.finditer(text):
                sentence = match.group(1).strip()
                start = match.start()
                end = match.end()

                # Extract what company can do vs what user can do
                company_power, user_power = analyze_clause_balance(sentence)

                imbalance = PowerImbalance(
                    category=category,
                    description=config["description"],
                    severity=config["severity"],
                    company_power=company_power,
                    user_power=user_power,
                    citation_text=sentence,
                    start_char=start,
                    end_char=end
                )
                imbalances.append(imbalance)

    # Remove duplicates based on citation overlap
    return deduplicate_by_position(imbalances)


def analyze_clause_balance(clause: str) -> Tuple[str, str]:
    """
    Analyze a clause to extract company powers vs user powers
    Returns (company_power, user_power)
    """
    clause_lower = clause.lower()

    # Company indicators
    company_indicators = ["we", "our", "us", "company", "service provider"]
    user_indicators = ["you", "your", "user", "customer", "subscriber"]

    # Check for modal verbs indicating power
    company_can = any(indicator in clause_lower for indicator in ["we may", "we can", "we reserve", "at our discretion"])
    user_must = any(indicator in clause_lower for indicator in ["you must", "you agree", "you shall", "you are required"])

    if company_can:
        company_power = "Can act at own discretion"
        user_power = "Must accept or leave service"
    elif user_must:
        company_power = "Sets requirements"
        user_power = "Must comply"
    else:
        company_power = "Controls terms"
        user_power = "Limited input"

    return company_power, user_power


def detect_data_issues(text: str) -> List[DataRightIssue]:
    """
    Detect data rights and privacy issues
    """
    issues = []

    for right_type, config in DATA_RIGHTS_PATTERNS.items():
        for keyword in config["keywords"]:
            pattern = re.compile(
                r'([^.!?]{0,200}' + re.escape(keyword) + r'[^.!?]{0,200}[.!?])',
                re.IGNORECASE
            )

            for match in pattern.finditer(text):
                sentence = match.group(1).strip()
                start = match.start()
                end = match.end()

                # Determine user control level
                user_control = assess_user_control(sentence, right_type)

                issue = DataRightIssue(
                    right_type=right_type,
                    description=f"Data {right_type} clause found",
                    user_control=user_control,
                    citation_text=sentence,
                    start_char=start,
                    end_char=end
                )
                issues.append(issue)

    return deduplicate_by_position(issues)


def assess_user_control(clause: str, right_type: str) -> str:
    """
    Assess how much control user has over their data
    Returns: "none", "limited", or "full"
    """
    clause_lower = clause.lower()

    # Positive control indicators
    positive_indicators = [
        "you can",
        "you may",
        "right to",
        "opt out",
        "opt-out",
        "choice",
        "consent"
    ]

    # Negative control indicators
    negative_indicators = [
        "we may",
        "without your consent",
        "automatically",
        "required",
        "necessary for service"
    ]

    has_positive = any(indicator in clause_lower for indicator in positive_indicators)
    has_negative = any(indicator in clause_lower for indicator in negative_indicators)

    if has_positive and not has_negative:
        return "full"
    elif has_positive and has_negative:
        return "limited"
    else:
        return "none"


def detect_consumer_red_flags(text: str) -> List[Dict[str, Any]]:
    """
    Detect consumer protection red flags
    """
    red_flags = []

    for flag_type, keywords in CONSUMER_RED_FLAGS.items():
        for keyword in keywords:
            pattern = re.compile(
                r'([^.!?]{0,200}' + re.escape(keyword) + r'[^.!?]{0,200}[.!?])',
                re.IGNORECASE
            )

            for match in pattern.finditer(text):
                red_flags.append({
                    "type": flag_type,
                    "text": match.group(1).strip(),
                    "start": match.start(),
                    "end": match.end()
                })

    return red_flags


def deduplicate_by_position(items: List) -> List:
    """
    Remove duplicate items based on overlapping positions
    """
    if not items:
        return items

    # Sort by start position
    sorted_items = sorted(items, key=lambda x: x.start_char)

    deduped = [sorted_items[0]]

    for item in sorted_items[1:]:
        last_item = deduped[-1]

        # If positions don't overlap significantly, add it
        overlap = min(last_item.end_char, item.end_char) - max(last_item.start_char, item.start_char)
        if overlap < 50:  # Less than 50 char overlap
            deduped.append(item)

    return deduped


def generate_policy_summary(
    text: str,
    doc_type: str,
    focus: str = "privacy"
) -> Dict[str, Any]:
    """
    Generate plain-language summary for ToS/Privacy Policy
    Focused on rights, risks, and power imbalances
    """
    # Detect all issues
    power_imbalances = detect_power_imbalances(text)
    data_issues = detect_data_issues(text)
    red_flags = detect_consumer_red_flags(text)

    # Categorize by severity
    high_risk_imbalances = [p for p in power_imbalances if p.severity == "high"]
    medium_risk_imbalances = [p for p in power_imbalances if p.severity == "medium"]

    # Data control assessment
    no_control_data = [d for d in data_issues if d.user_control == "none"]
    limited_control_data = [d for d in data_issues if d.user_control == "limited"]

    summary = {
        "doc_type": doc_type,
        "focus": focus,
        "analysis_type": "policy_analysis",

        "power_imbalances": {
            "total": len(power_imbalances),
            "high_severity": len(high_risk_imbalances),
            "medium_severity": len(medium_risk_imbalances),
            "items": [
                {
                    "category": p.category,
                    "description": p.description,
                    "severity": p.severity,
                    "company_power": p.company_power,
                    "user_power": p.user_power,
                    "citation": {
                        "text": p.citation_text,
                        "start": p.start_char,
                        "end": p.end_char
                    }
                }
                for p in power_imbalances[:10]  # Limit to top 10
            ]
        },

        "data_rights": {
            "total_issues": len(data_issues),
            "no_control": len(no_control_data),
            "limited_control": len(limited_control_data),
            "items": [
                {
                    "type": d.right_type,
                    "description": d.description,
                    "user_control": d.user_control,
                    "citation": {
                        "text": d.citation_text,
                        "start": d.start_char,
                        "end": d.end_char
                    }
                }
                for d in data_issues[:10]
            ]
        },

        "consumer_red_flags": {
            "total": len(red_flags),
            "items": red_flags[:5]  # Top 5
        },

        "key_takeaways": generate_key_takeaways(
            power_imbalances,
            data_issues,
            red_flags,
            doc_type
        ),

        "disclaimer": "This is a plain-language analysis for educational purposes only. "
                     "It is NOT legal advice. The power imbalances and risks identified are "
                     "based on automated text analysis. Consult a qualified attorney for "
                     "legal advice specific to your situation."
    }

    return summary


def generate_key_takeaways(
    power_imbalances: List[PowerImbalance],
    data_issues: List[DataRightIssue],
    red_flags: List[Dict],
    doc_type: str
) -> List[str]:
    """
    Generate plain-language key takeaways
    """
    takeaways = []

    # Power imbalances
    if power_imbalances:
        high_severity = [p for p in power_imbalances if p.severity == "high"]
        if high_severity:
            takeaways.append(
                f"The company retains significant power to change terms, limit liability, "
                f"and control your access ({len(high_severity)} high-risk clauses found)."
            )

    # Data control
    no_control = [d for d in data_issues if d.user_control == "none"]
    if no_control:
        takeaways.append(
            f"You have limited or no control over {len(no_control)} types of data usage."
        )

    # Forced arbitration
    arbitration = [p for p in power_imbalances if p.category == "forced_arbitration"]
    if arbitration:
        takeaways.append(
            "You may be waiving your right to sue or participate in class action lawsuits."
        )

    # Red flags
    if red_flags:
        takeaways.append(
            f"Found {len(red_flags)} consumer protection concerns (fees, refunds, auto-renewal)."
        )

    # Always add this
    takeaways.append(
        "By using the service, you agree to these terms. Consider whether the trade-offs are acceptable."
    )

    return takeaways
