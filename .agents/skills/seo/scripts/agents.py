"""Known AI crawler user agents, grouped by what blocking them costs you.

Verify against each operator's own published crawler documentation at run time.
Agent names change and operators add new ones. This list is a starting point for
that check, not the authority.

  retrieval     fetches at answer time, or builds the index the engine searches.
                blocking it removes you from that engine's answers.
  user          fetches one page because a person asked the assistant to read it.
                blocking it breaks "read this link for me" on your site.
  training      collects content to train future models.
                blocking it is a business decision. it does not affect today's answers.
"""

AGENTS = [
    # OpenAI
    ("OAI-SearchBot",   "OpenAI",     "retrieval", "powers ChatGPT search results"),
    ("ChatGPT-User",    "OpenAI",     "user",      "user-triggered page fetch"),
    ("GPTBot",          "OpenAI",     "training",  "training crawler"),
    # Anthropic
    ("ClaudeBot",       "Anthropic",  "retrieval", "crawler"),
    ("Claude-SearchBot","Anthropic",  "retrieval", "search indexing"),
    ("Claude-User",     "Anthropic",  "user",      "user-triggered page fetch"),
    ("anthropic-ai",    "Anthropic",  "training",  "older agent name, still seen"),
    # Google
    ("Googlebot",       "Google",     "retrieval", "the index AI Overviews and AI Mode draw from"),
    ("Google-Extended", "Google",     "training",  "Gemini training and grounding. does NOT gate AI Overviews"),
    ("GoogleOther",     "Google",     "training",  "misc Google crawling"),
    # Perplexity
    ("PerplexityBot",   "Perplexity", "retrieval", "indexing"),
    ("Perplexity-User", "Perplexity", "user",      "user-triggered page fetch"),
    # Microsoft
    ("bingbot",         "Microsoft",  "retrieval", "the index Copilot draws from"),
    # Apple
    ("Applebot",        "Apple",      "retrieval", "Siri and Spotlight suggestions"),
    ("Applebot-Extended","Apple",     "training",  "training opt-out control"),
    # Broad crawlers whose data flows downstream into many systems
    ("CCBot",           "CommonCrawl","training",  "feeds many downstream datasets. broad, delayed effects"),
    ("Amazonbot",       "Amazon",     "retrieval", "Alexa and Amazon surfaces"),
    ("meta-externalagent", "Meta",    "training",  "Meta AI training"),
    ("Bytespider",      "ByteDance",  "training",  "ByteDance crawler"),
    ("cohere-ai",       "Cohere",     "training",  "Cohere crawler"),
    ("Diffbot",         "Diffbot",    "training",  "knowledge graph extraction"),
    ("omgilibot",       "Webz.io",    "training",  "web data collection"),
    ("YouBot",          "You.com",    "retrieval", "You.com search"),
    ("AI2Bot",          "AI2",        "training",  "Allen Institute crawler"),
    ("Timpibot",        "Timpi",      "training",  "decentralised index"),
]

# Referrer hosts that indicate a click from a generated answer.
REFERRER_HOSTS = [
    ("chatgpt.com",              "ChatGPT"),
    ("chat.openai.com",          "ChatGPT"),
    ("openai.com",               "OpenAI"),
    ("perplexity.ai",            "Perplexity"),
    ("www.perplexity.ai",        "Perplexity"),
    ("claude.ai",                "Claude"),
    ("gemini.google.com",        "Gemini"),
    ("bard.google.com",          "Gemini"),
    ("copilot.microsoft.com",    "Copilot"),
    ("www.bing.com/chat",        "Copilot"),
    ("edgeservices.bing.com",    "Copilot"),
    ("you.com",                  "You.com"),
    ("poe.com",                  "Poe"),
    ("phind.com",                "Phind"),
]


def classify(ua_string):
    """Return (agent_name, vendor, kind) for a raw user-agent string, or None."""
    low = (ua_string or "").lower()
    best = None
    for name, vendor, kind, _desc in AGENTS:
        if name.lower() in low:
            # prefer the longest matching token so Claude-SearchBot beats ClaudeBot
            if best is None or len(name) > len(best[0]):
                best = (name, vendor, kind)
    return best


def referrer_engine(referrer):
    """Return the engine name for a referrer URL, or None."""
    low = (referrer or "").lower()
    for host, label in REFERRER_HOSTS:
        if host in low:
            return label
    return None
