"""Tests für das Kritiker- und Revisionssystem (plan2.md Stufe 11)."""

from __future__ import annotations

from au.analysis.metrics import MusicalQualityReport
from au.integrator.revision import run_revision_loop


def test_revision_loop_accepted_report() -> None:
    report = MusicalQualityReport(
        peak_dbfs=-6.0,
        rms_dbfs=-19.0,
        lufs_estimated=-16.0,
        active_signal_ratio=0.9,
        harmonic_energy_ratio=0.3,
        dc_offset=0.0,
        clip_ratio=0.0,
        click_count=0,
        accepted=True,
        reasons=(),
    )
    res = run_revision_loop(report)
    assert res.accepted is True
    assert len(res.proposals) == 0


def test_revision_loop_rejected_report() -> None:
    report = MusicalQualityReport(
        peak_dbfs=-40.0,
        rms_dbfs=-45.0,
        lufs_estimated=-42.0,
        active_signal_ratio=0.9,
        harmonic_energy_ratio=0.3,
        dc_offset=0.0,
        clip_ratio=0.0,
        click_count=0,
        accepted=False,
        reasons=("Signal zu leise (-42.0 LUFS < -28.0 LUFS)",),
    )
    res = run_revision_loop(report)
    assert len(res.proposals) > 0
    assert res.proposals[0].kind == "rebalance_stem"
