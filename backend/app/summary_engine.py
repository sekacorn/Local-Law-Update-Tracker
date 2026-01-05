"""
Plain-language summary engine
Helps non-lawyers understand complex legal documents
"""
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class Citation:
    """Citation to source text"""
    text: str
    start_char: int
    end_char: int
    context: str


@dataclass
class Warning:
    """Liability or risk warning"""
    category: str  # e.g., "liability", "deadline", "penalty", "waiver"
    description: str
    risk_level: str  # "low", "medium", "high"
    citation: Citation
    who_affected: str  # e.g., "you", "employer", "both parties"


# Common legal terms and their plain-language equivalents
PLAIN_LANGUAGE_TERMS = {
    "herein": "in this document",
    "hereinafter": "from now on in this document",
    "aforementioned": "mentioned earlier",
    "pursuant to": "according to",
    "notwithstanding": "despite",
    "whereby": "by which",
    "thereof": "of it",
    "therein": "in it",
    "henceforth": "from now on",
    "forthwith": "immediately",
    "heretofore": "before now",
    "inter alia": "among other things",
    "ipso facto": "by that very fact",
    "prima facie": "at first glance",
    "quid pro quo": "something for something",
    "vis-a-vis": "in relation to",
}


# Risk/liability keywords to detect
RISK_KEYWORDS = {
    "liability": ["liable", "liability", "responsible for damages", "indemnify", "hold harmless"],
    "deadline": ["within", "days", "deadline", "expire", "no later than", "must be completed by"],
    "penalty": ["penalty", "fine", "fee", "charge", "late fee", "forfeiture", "damages"],
    "waiver": ["waive", "waiver", "give up", "relinquish", "forfeit"],
    "termination": ["terminate", "termination", "cancel", "cancellation", "end", "discontinue"],
    "arbitration": ["arbitration", "arbitrator", "binding arbitration", "waive right to sue"],
    "class_action": ["class action", "collective action", "representative action"],
    "confidentiality": ["confidential", "non-disclosure", "secret", "proprietary"],
}


def simplify_language(text: str) -> str:
    """
    Replace legal jargon with plain language
    """
    simplified = text

    for legal_term, plain_term in PLAIN_LANGUAGE_TERMS.items():
        # Case-insensitive replacement
        pattern = re.compile(re.escape(legal_term), re.IGNORECASE)
        simplified = pattern.sub(plain_term, simplified)

    return simplified


def detect_warnings(text: str, doc_type: str = "general") -> List[Warning]:
    """
    Detect liability and risk warnings in the document
    """
    warnings = []
    text_lower = text.lower()

    for category, keywords in RISK_KEYWORDS.items():
        for keyword in keywords:
            # Find all occurrences
            pattern = re.compile(r'([^.]*?' + re.escape(keyword) + r'[^.]*\.)', re.IGNORECASE)
            matches = pattern.finditer(text)

            for match in matches:
                sentence = match.group(1).strip()
                start_pos = match.start()
                end_pos = match.end()

                # Get context (surrounding sentences)
                context_start = max(0, start_pos - 200)
                context_end = min(len(text), end_pos + 200)
                context = text[context_start:context_end].strip()

                # Determine risk level based on keywords
                risk_level = "medium"
                if any(word in sentence.lower() for word in ["must", "shall", "required", "mandatory"]):
                    risk_level = "high"
                elif any(word in sentence.lower() for word in ["may", "can", "optional"]):
                    risk_level = "low"

                # Determine who is affected
                who_affected = "you"
                if "employer" in sentence.lower() or "company" in sentence.lower():
                    who_affected = "employer"
                if "both parties" in sentence.lower() or "each party" in sentence.lower():
                    who_affected = "both parties"

                # Create description
                description = _create_warning_description(category, sentence)

                warning = Warning(
                    category=category,
                    description=description,
                    risk_level=risk_level,
                    citation=Citation(
                        text=sentence,
                        start_char=start_pos,
                        end_char=end_pos,
                        context=context
                    ),
                    who_affected=who_affected
                )

                warnings.append(warning)
                break  # Only one warning per keyword per category

    return warnings[:10]  # Limit to 10 warnings


def _create_warning_description(category: str, sentence: str) -> str:
    """Create plain-language description of a warning"""
    descriptions = {
        "liability": "This clause may make you responsible for damages or losses. You could be held financially liable.",
        "deadline": "This sets a time limit. Missing this deadline could have consequences.",
        "penalty": "This describes fees or charges you may have to pay under certain conditions.",
        "waiver": "This means you're giving up certain rights. Once waived, these rights may be hard to recover.",
        "termination": "This describes how the agreement can be ended and what happens when it ends.",
        "arbitration": "This may limit your ability to sue in court. Disputes may be resolved through arbitration instead.",
        "class_action": "This may prevent you from joining class action lawsuits.",
        "confidentiality": "This requires you to keep certain information secret. Sharing it could have legal consequences.",
    }

    return descriptions.get(category, "Important clause that may affect your rights or obligations.")


def generate_questions(text: str, doc_type: str, focus: str = "general") -> List[str]:
    """
    Generate "questions to ask a professional" based on document type and focus
    """
    questions = []

    # General questions for all documents
    questions.extend([
        "What are my obligations under this document?",
        "What rights am I giving up by signing this?",
        "What happens if I need to end this agreement?",
    ])

    # Focus-specific questions
    if focus == "home_buying":
        questions.extend([
            "Are there any hidden fees or costs not mentioned upfront?",
            "What inspections or disclosures am I entitled to?",
            "What happens if the sale falls through?",
            "Am I responsible for repairs before or after closing?",
        ])
    elif focus == "job_hr":
        questions.extend([
            "Does this restrict my ability to work elsewhere after leaving?",
            "What benefits am I entitled to and when do they start?",
            "Under what conditions can my employment be terminated?",
            "Am I required to keep company information confidential?",
        ])

    # Add questions based on detected content
    if "arbitration" in text.lower():
        questions.append("Am I giving up my right to sue in court by agreeing to arbitration?")

    if "non-compete" in text.lower() or "non-solicitation" in text.lower():
        questions.append("How long and how broadly does this non-compete clause restrict me?")

    return questions[:8]  # Limit to 8 questions


def generate_summary(
    text: str,
    title: str,
    doc_type: str,
    focus: str = "general",
    max_length: str = "medium"
) -> Dict[str, Any]:
    """
    Generate a plain-language summary of a legal document

    Args:
        text: Document text
        title: Document title
        doc_type: Type of document (bill, executive_order, opinion, etc.)
        focus: Focus area (general, home_buying, job_hr, etc.)
        max_length: Summary length (short, medium, long)

    Returns:
        Dictionary with summary sections, warnings, and citations
    """

    # Check if this is a policy document (ToS, Privacy Policy, etc.)
    policy_types = ["Terms of Service", "Privacy Policy", "User Agreement", "EULA"]
    if doc_type in policy_types or focus in ["privacy", "consumer"]:
        # Use specialized policy analyzer
        from .analysis.policy_analyzer import generate_policy_summary
        return generate_policy_summary(text, doc_type, focus)

    # Detect warnings and risks
    warnings = detect_warnings(text, doc_type)

    # Generate questions
    questions = generate_questions(text, doc_type, focus)

    # Extract key information
    summary_sections = []

    # 1. What this document is
    doc_type_descriptions = {
        "executive_order": "a directive from the President",
        "bill": "proposed legislation that may become law",
        "opinion": "a court decision interpreting the law",
        "regulation": "a rule created by a government agency",
    }

    what_it_is = doc_type_descriptions.get(doc_type, "a legal document")

    summary_sections.append({
        "heading": "What This Is",
        "content": f"This is {what_it_is}. It is titled \"{title}\".",
        "citations": []
    })

    # 2. Key points (extract from first 500 chars)
    preview = text[:500].strip()
    if len(preview) > 0:
        summary_sections.append({
            "heading": "Overview",
            "content": simplify_language(preview),
            "citations": [{"start": 0, "end": min(500, len(text))}]
        })

    # 3. Who this affects
    affected_text = "This may affect citizens, government agencies, or specific groups mentioned in the document."
    if "employee" in text.lower():
        affected_text = "This affects employees and employers."
    elif "homeowner" in text.lower() or "property" in text.lower():
        affected_text = "This may affect property owners and buyers."

    summary_sections.append({
        "heading": "Who This Affects",
        "content": affected_text,
        "citations": []
    })

    # 4. Important warnings
    if warnings:
        warning_content = f"This document contains {len(warnings)} important clauses you should be aware of. "
        warning_content += "See the Warnings section below for details."

        summary_sections.append({
            "heading": "Important Notices",
            "content": warning_content,
            "citations": []
        })

    # Coverage calculation
    coverage = {
        "full_text_analyzed": len(text) > 0,
        "text_length": len(text),
        "warnings_detected": len(warnings),
        "sections_analyzed": len(summary_sections)
    }

    return {
        "summary_sections": summary_sections,
        "warnings": [
            {
                "category": w.category,
                "description": w.description,
                "risk_level": w.risk_level,
                "who_affected": w.who_affected,
                "citation_text": w.citation.text,
                "citation_context": w.citation.context
            }
            for w in warnings
        ],
        "questions_for_professional": questions,
        "coverage": coverage,
        "disclaimer": "This is NOT legal advice. This summary is for educational purposes only. "
                     "Consult a qualified attorney for legal advice specific to your situation."
    }


def explain_section(
    text: str,
    selection: str,
    question: Optional[str] = None
) -> Dict[str, Any]:
    """
    Explain a specific section of text in plain language

    Args:
        text: Full document text
        selection: Selected text to explain (heading or specific passage)
        question: Optional specific question about the selection

    Returns:
        Explanation with citations
    """

    # Find the selection in the text
    selection_lower = selection.lower()
    text_lower = text.lower()

    start_pos = text_lower.find(selection_lower)

    if start_pos == -1:
        return {
            "error": "Selection not found in document",
            "explanation": None
        }

    end_pos = start_pos + len(selection)

    # Get context around the selection
    context_start = max(0, start_pos - 300)
    context_end = min(len(text), end_pos + 300)
    context = text[context_start:context_end]

    # Simplify the selected text
    simplified = simplify_language(selection)

    # Create explanation
    explanation = f"In plain language: {simplified}"

    # Add specific question answer if provided
    if question:
        explanation += f"\n\nRegarding your question \"{question}\": "
        explanation += "This section addresses that concern. Please consult an attorney for specific guidance."

    return {
        "selection": selection,
        "explanation": explanation,
        "simplified_text": simplified,
        "citation": {
            "start_char": start_pos,
            "end_char": end_pos,
            "context": context
        },
        "disclaimer": "This explanation is for educational purposes only and is not legal advice."
    }
