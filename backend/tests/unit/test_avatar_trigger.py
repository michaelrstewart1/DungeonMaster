"""Avatar auto-animation — narration triggers the speaking state."""
from app.api.routes import avatar as avatar_module
from app.api.routes.avatar import trigger_speaking


class TestTriggerSpeaking:
    def setup_method(self):
        avatar_module.reset()

    def test_sets_speaking_window(self):
        trigger_speaking("sess-1", "The dragon unleashes a torrent of flame upon the bridge!")
        state = avatar_module._get_or_create_state("sess-1")
        assert state.is_speaking is True
        assert state.mouth_amplitude > 0
        assert "sess-1" in avatar_module._speaking_timers

    def test_expression_follows_sentiment(self):
        trigger_speaking("sess-2", "A shadow of doom and terror falls across the demon-haunted crypt.")
        state = avatar_module._get_or_create_state("sess-2")
        assert state.expression.value == "menacing"

    def test_empty_text_is_noop(self):
        trigger_speaking("sess-3", "")
        assert "sess-3" not in avatar_module._speaking_timers

    def test_duration_scales_with_length(self):
        from datetime import datetime
        trigger_speaking("short", "Hello there.")
        trigger_speaking("long", " ".join(["word"] * 100))
        now = datetime.now()
        short_left = (avatar_module._speaking_timers["short"] - now).total_seconds()
        long_left = (avatar_module._speaking_timers["long"] - now).total_seconds()
        assert long_left > short_left
