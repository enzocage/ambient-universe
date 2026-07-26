from pathlib import Path

import pytest

from au.learning.active_selector import ActiveLearningSelector, LearningCandidate
from au.learning.presentation_memory import Presentation, PresentationMemory
from au.learning.rating import RatingStore


def test_rating_store_persists_1_to_10_events(tmp_path: Path) -> None:
    path = tmp_path / "ratings.json"
    store = RatingStore(path)
    event = store.add(
        presentation_id="p1",
        candidate_id="bass-a",
        audio_fingerprint="audio-a",
        role="bass_sequence",
        context="peak",
        rating=9,
    )
    assert RatingStore(path).mean_for("bass-a", role="bass_sequence") == 9
    assert event.rating == 9
    with pytest.raises(ValueError):
        store.add(
            presentation_id="p2", candidate_id="bad", audio_fingerprint="bad",
            role="bass_sequence", context="peak", rating=11,
        )


def test_memory_and_selector_prioritize_new_informative_audio() -> None:
    memory = PresentationMemory()
    memory.remember(Presentation("p1", "old", "same-audio", "synth.a", "preset-a", "intro"))
    selector = ActiveLearningSelector(RatingStore(), memory)
    candidates = [
        LearningCandidate("old", "same-audio", "bass_sequence", "intro", 0.95, novelty=1.0),
        LearningCandidate("new", "new-audio", "bass_sequence", "peak", 0.90, novelty=1.0, uncertainty=1.0),
    ]
    assert [item.candidate_id for item in selector.select(candidates)] == ["new"]
