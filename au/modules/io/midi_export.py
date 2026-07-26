"""MIDI-Export der Elementansteuerung (plan.md io.midi.export)."""

from __future__ import annotations

from pathlib import Path

from au.dsl.element import ElementRecipe
from au.dsl.pattern import NoteEvent


def export_midi(events: list[NoteEvent], recipe: ElementRecipe, output_path: Path) -> Path:
    """Schreibt die Ereignisse eines Elements als Standard-MIDI-Datei."""
    import mido

    ticks_per_beat = 480
    # Ein fixes, moderates Tempo: die Ereigniszeiten selbst tragen die
    # eigentliche Information, das Tempo dient nur der DAW-Anzeige.
    bpm = 60.0
    seconds_per_tick = 60.0 / (bpm * ticks_per_beat)

    track = mido.MidiTrack()
    midi_events: list[tuple[int, mido.Message]] = []
    for event in events:
        pitch = int(round(event.pitch_midi(recipe.field)))
        pitch = max(0, min(127, pitch))
        velocity = max(1, min(127, int(round(event.velocity * 127))))
        start_tick = int(round(event.time_s / seconds_per_tick))
        end_tick = int(round((event.time_s + event.duration_s) / seconds_per_tick))
        midi_events.append((start_tick, mido.Message("note_on", note=pitch, velocity=velocity)))
        midi_events.append((end_tick, mido.Message("note_off", note=pitch, velocity=0)))

    midi_events.sort(key=lambda pair: pair[0])
    last_tick = 0
    for tick, msg in midi_events:
        msg.time = max(0, tick - last_tick)
        track.append(msg)
        last_tick = tick

    midi_file = mido.MidiFile(ticks_per_beat=ticks_per_beat)
    midi_file.tracks.append(track)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    midi_file.save(str(output_path))
    return output_path
