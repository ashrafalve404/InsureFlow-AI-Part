"""
Application-wide constants for the Real-Time AI Sales Assistant backend.
"""

# Call session statuses
class CallStatus:
    ACTIVE = "active"
    ENDED = "ended"


# Speaker roles in a transcript
class Speaker:
    AGENT = "agent"
    CUSTOMER = "customer"


# Objection labels
class ObjectionLabel:
    PRICE = "price"
    NOT_INTERESTED = "not_interested"
    NEEDS_TIME = "needs_time"
    ALREADY_HAVE_SOLUTION = "already_have_solution"
    HESITANT = "hesitant"
    NONE = "none"


# Call stage labels
class CallStage:
    OPENING = "opening"
    DISCOVERY = "discovery"
    QUALIFICATION = "qualification"
    PITCH = "pitch"
    OBJECTION_HANDLING = "objection_handling"
    CLOSING = "closing"
    UNKNOWN = "unknown"


# Compliance risk phrases (rule-based triggers)
COMPLIANCE_RISK_PHRASES = [
    "guaranteed",
    "guarantee",
    "no risk",
    "100% sure",
    "100 percent sure",
    "promise you",
    "i promise",
    "we promise",
    "absolutely certain",
    "risk free",
    "risk-free",
    "zero risk",
    "without fail",
    "definitely will",
]

# Objection keyword mapping for rule-based detection
OBJECTION_KEYWORDS = {
    ObjectionLabel.PRICE: [
        "too expensive",
        "cost too much",
        "can't afford",
        "price is high",
        "too costly",
        "out of budget",
        "cheaper option",
        "price",
        "expensive",
    ],
    ObjectionLabel.NOT_INTERESTED: [
        "not interested",
        "don't care",
        "no thank you",
        "no thanks",
        "not for me",
        "pass on this",
        "not relevant",
    ],
    ObjectionLabel.NEEDS_TIME: [
        "need to think",
        "give me time",
        "not ready",
        "call me later",
        "think about it",
        "get back to you",
        "not right now",
    ],
    ObjectionLabel.ALREADY_HAVE_SOLUTION: [
        "already have",
        "using another",
        "have a provider",
        "current solution",
        "working with someone",
        "already covered",
    ],
    ObjectionLabel.HESITANT: [
        "not sure",
        "unsure",
        "maybe",
        "possibly",
        "sounds risky",
        "worried",
        "concern",
        "hesitate",
    ],
}

# Max recent transcript chunks to send to AI for context
MAX_CONTEXT_CHUNKS = 10

# Default AI model
DEFAULT_AI_MODEL = "gpt-4o-mini"
