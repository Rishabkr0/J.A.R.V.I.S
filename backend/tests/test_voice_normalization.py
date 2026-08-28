import pytest
from app.voice.normalization import TranscriptNormalizer
from app.orchestrator.fast_router import FastRouter, Intent

@pytest.fixture
def normalizer():
    return TranscriptNormalizer()

@pytest.fixture
def router():
    return FastRouter()

def test_exact_commands(normalizer, router):
    phrases = [
        ("What window is active?", Intent.GET_ACTIVE_WINDOW),
        ("Which window is active?", Intent.GET_ACTIVE_WINDOW),
        ("What application is active?", Intent.GET_ACTIVE_WINDOW),
        ("Which app is active?", Intent.GET_ACTIVE_WINDOW),
        ("read my screen", Intent.GET_VISIBLE_TEXT),
        ("read the screen", Intent.GET_VISIBLE_TEXT),
        ("whats on my screen", Intent.GET_SCREEN_STATE),
        ("what is on my screen", Intent.GET_SCREEN_STATE),
        ("take a screenshot", Intent.CAPTURE_SCREEN),
        ("open chrome", Intent.OPEN_BROWSER),
        ("open notepad", Intent.OPEN_APP),
    ]
    for raw, expected_intent in phrases:
        norm = normalizer.normalize(raw)
        res = router.parse(norm)
        assert res is not None, f"Failed to route '{raw}' (norm: '{norm}')"
        assert res[0] == expected_intent, f"Expected {expected_intent} for '{raw}', got {res[0]}"

def test_phonetic_stt_recovery(normalizer, router):
    # Test Whisper acoustic misrecognition recovery
    misrecognitions = [
        ("What we do is active.", Intent.GET_ACTIVE_WINDOW),
        ("What when do is active", Intent.GET_ACTIVE_WINDOW),
        ("reed my screen", Intent.GET_VISIBLE_TEXT),
    ]
    for raw, expected_intent in misrecognitions:
        norm = normalizer.normalize(raw)
        res = router.parse(norm)
        assert res is not None, f"Failed to recover misrecognition '{raw}' (norm: '{norm}')"
        assert res[0] == expected_intent

def test_conversational_safety(normalizer, router):
    # Ordinary sentences containing command words MUST NOT trigger computer actions
    conversational_sentences = [
        "I was talking about an active window yesterday",
        "My active window has a nice wallpaper",
        "I read something on my screen earlier today",
        "We should take a screenshot of that website next week",
        "He told me to open chrome when I get home",
    ]
    for sentence in conversational_sentences:
        norm = normalizer.normalize(sentence)
        res = router.parse(norm)
        # Should either normalize to conversational sentence or fail to match local intent
        assert res is None, f"Safety violation! Sentence '{sentence}' was wrongly routed to local intent '{res[0]}'"
