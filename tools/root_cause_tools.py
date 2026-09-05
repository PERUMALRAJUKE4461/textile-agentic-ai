"""Evidence-based root-cause analysis for textile loom faults."""

from collections.abc import Iterable
from typing import Any

from tools.diagnostic_tools import diagnose_machine
from tools.machine_tools import get_machine_status
from tools.maintenance_tools import get_maintenance_history
from tools.research_tools import web_research


OBSERVED_FACT = "OBSERVED FACT"
WEB_REFERENCE = "WEB REFERENCE"
INFERENCE = "INFERENCE"
RECOMMENDATION = "RECOMMENDATION"


def _maintenance_text(history: dict[str, Any]) -> str:
    """Return maintenance fields as searchable text."""
    return " ".join(
        str(value).lower()
        for record in history.get("records", [])
        for value in record.values()
    )


def _fact(label: str, value: Any) -> dict[str, str]:
    return {"type": OBSERVED_FACT, "detail": f"{label}: {value}"}


def _reference(result: dict[str, Any]) -> dict[str, str]:
    return {
        "type": WEB_REFERENCE,
        "title": str(result.get("title", "")),
        "url": str(result.get("url", "")),
        "detail": str(result.get("content", "")),
    }


def build_research_queries(
    machine: dict[str, Any], diagnosis: dict[str, Any]
) -> list[str]:
    """Build focused technical queries from observed fault indicators."""
    loom_type = str(machine.get("loom_type", "textile loom"))
    fault = str(machine.get("fault_type", "")).replace("_", " ").lower()
    issues = [str(issue).lower() for issue in diagnosis.get("issues", [])]
    indicators = " ".join(dict.fromkeys([fault, *issues])).strip()
    if not indicators:
        indicators = "normal operation"

    queries = [
        f"{loom_type} {indicators} causes troubleshooting",
    ]
    if "low production" in indicators or "efficiency" in indicators:
        queries.append(
            f"{loom_type} low production compressed air pressure nozzle problems"
        )
    if "defect" in indicators or "tension" in indicators:
        queries.append(
            f"{loom_type} high defect rate weft insertion troubleshooting"
        )
    if "vibration" in indicators or "temperature" in indicators:
        queries.append(
            f"{loom_type} abnormal vibration bearing temperature causes"
        )
    return list(dict.fromkeys(queries))


def _research_for_cause(
    cause: str, research: Iterable[dict[str, Any]]
) -> list[dict[str, str]]:
    """Select references whose text is relevant to a suspected cause."""
    terms = set(cause.lower().replace("/", " ").split())
    selected = []
    for result in research:
        searchable = (
            f"{result.get('title', '')} {result.get('content', '')}"
        ).lower()
        if terms.intersection(searchable.split()) or not selected:
            selected.append(_reference(result))
    return selected[:3]


def _score(base: int, support_count: int, contradiction_count: int) -> int:
    """Calculate a bounded evidence score, not a statistical probability."""
    return max(0, min(100, base + support_count * 12 - contradiction_count * 8))


def _candidate(
    name: str,
    score: int,
    observations: list[dict[str, str]],
    maintenance: list[dict[str, str]],
    research: list[dict[str, str]],
    missing: list[str],
    inference: str,
    recommendations: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "cause": name,
        "confidence_score": max(0, min(100, score)),
        "confidence_label": "evidence-based confidence score, not a probability",
        "evidence": {
            "supporting_machine_observations": observations,
            "relevant_maintenance_history": maintenance,
            "supporting_web_research": research,
            "contradicting_or_missing_evidence": [
                {"type": INFERENCE, "detail": item} for item in missing
            ],
            "inference": {"type": INFERENCE, "detail": inference},
        },
        "recommendations": [
            {"priority": priority, "type": RECOMMENDATION, "action": action}
            for priority, action in recommendations
        ],
    }


def analyze_root_causes(
    machine: dict[str, Any],
    maintenance: dict[str, Any],
    diagnosis: dict[str, Any],
    research: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Correlate machine facts, history, diagnostics, and web references.

    The function only reports values supplied by the local tools as observed
    facts. Web results are kept under a separate reference field and never
    become machine measurements.
    """
    if not machine.get("success", False):
        return machine

    research = research or []
    maintenance_text = _maintenance_text(maintenance)
    issues = {str(issue).lower() for issue in diagnosis.get("issues", [])}
    candidates: list[dict[str, Any]] = []

    def add_candidate(
        name: str,
        base: int,
        observations: list[dict[str, str]],
        history_terms: list[str],
        missing: list[str],
        inference: str,
        recommendations: list[tuple[int, str]],
        support_count: int,
    ) -> None:
        history_facts = []
        for record in maintenance.get("records", []):
            detail = "; ".join(
                f"{key}: {value}" for key, value in record.items()
            )
            if any(term in detail.lower() for term in history_terms):
                history_facts.append(_fact("Maintenance record", detail))
        evidence_gaps = list(missing)
        if not research:
            evidence_gaps.append(
                "No successful web research was available for this suspected cause."
            )
        if not observations and not history_facts:
            return
        candidates.append(
            _candidate(
                name,
                _score(base, support_count + len(history_facts), len(missing)),
                observations,
                history_facts,
                _research_for_cause(name, research),
                evidence_gaps,
                inference,
                recommendations,
            )
        )

    loom_type = str(machine.get("loom_type", "")).lower()
    is_air_jet = "air" in loom_type and "jet" in loom_type
    low_production = (
        machine.get("production_rate", 100) < 85
        or machine.get("efficiency", 100) < 85
        or "low production" in issues
    )
    high_defect = machine.get("defect_rate", 0) > 2 or "high defect rate" in issues

    if is_air_jet and low_production:
        observations = [
            _fact("Loom type", machine["loom_type"]),
            _fact("Production rate", machine["production_rate"]),
            _fact("Efficiency", machine["efficiency"]),
        ]
        add_candidate(
            "Air supply problem",
            48,
            observations,
            ["air", "pressure", "production"],
            ["No direct compressed-air pressure measurement is available."],
            "The air-jet process and reduced output are consistent with an air-supply restriction, but pressure must be measured on the machine.",
            [
                (1, "Measure compressor and main-line pressure at the loom while running."),
                (2, "Inspect the air filter, regulator, hoses, and fittings for restriction or leakage."),
                (3, "Trend pressure against production rate during a controlled run."),
            ],
            2,
        )
        add_candidate(
            "Weft insertion problem",
            44,
            observations + [_fact("Fault type", machine.get("fault_type", "not reported"))],
            ["weft insertion", "production"],
            ["The telemetry does not identify the failed insertion component."],
            "Reduced output on an air-jet loom can be consistent with unstable weft insertion; the insertion path needs a direct inspection.",
            [
                (1, "Inspect weft insertion timing, sensors, and the insertion path for stoppage marks."),
                (2, "Check nozzle alignment and valve response during insertion cycles."),
                (3, "Review stop causes and compare insertion faults with the production trend."),
            ],
            2,
        )
        add_candidate(
            "Nozzle or valve issue",
            38,
            observations,
            ["nozzle", "valve", "pressure"],
            ["Nozzle flow and valve response were not measured by the telemetry tool."],
            "Low output on an air-jet loom is compatible with restricted nozzle flow or a slow valve, but this remains an unverified inference.",
            [
                (1, "Check nozzle cleanliness, alignment, and flow at operating pressure."),
                (2, "Test solenoid valve actuation and inspect seals for leakage."),
                (3, "Compare nozzle flow and valve timing with the loom service specification."),
            ],
            1,
        )

    if machine.get("vibration", 0) > 3 or "high vibration" in issues or machine.get("fault_type") == "BEARING_FAULT":
        observations = [
            _fact("Vibration", machine["vibration"]),
            _fact("Temperature", machine["temperature"]),
            _fact("Motor current", machine["motor_current"]),
        ]
        add_candidate(
            "Mechanical or bearing issue",
            60,
            observations,
            ["vibration", "bearing", "lubrication"],
            ["Bearing condition and lubricant state require physical inspection."],
            "The combined vibration, thermal, or current observations are consistent with mechanical resistance or bearing degradation.",
            [
                (1, "Stop or isolate the loom if vibration is worsening, then inspect bearing temperature and play."),
                (2, "Check lubrication level, alignment, coupling, and bearing noise."),
                (3, "Trend vibration and motor current after corrective maintenance."),
            ],
            2,
        )

    if machine.get("temperature", 0) > 65 or "high temperature" in issues:
        add_candidate(
            "Cooling or thermal issue",
            55,
            [_fact("Temperature", machine["temperature"]), _fact("Efficiency", machine["efficiency"])],
            ["temperature", "cooling", "overheating"],
            ["Ambient temperature and airflow were not supplied."],
            "The elevated temperature is observed; the cause may be cooling, overload, or mechanical drag and needs separation by inspection.",
            [
                (1, "Verify safe temperature and inspect cooling airflow before continued operation."),
                (2, "Clean cooling paths and check fan operation and motor load."),
                (3, "Compare temperature with ambient conditions and post-maintenance current."),
            ],
            2,
        )

    if high_defect or "abnormal warp tension" in issues or "abnormal weft tension" in issues:
        observations = [_fact("Defect rate", machine["defect_rate"])]
        for key in ("warp_tension", "weft_tension"):
            if key in machine:
                observations.append(_fact(key.replace("_", " ").title(), machine[key]))
        add_candidate(
            "Yarn tension or weft process issue",
            50,
            observations,
            ["tension", "weft", "yarn"],
            ["The telemetry cannot distinguish tension drift from downstream insertion defects."],
            "The elevated defect or tension observation is consistent with unstable yarn control or weft handling.",
            [
                (1, "Check warp and weft tension against the loom setup and inspect yarn path drag."),
                (2, "Verify tension sensors and calibrate the controller if readings are out of range."),
                (3, "Run a controlled fabric sample and correlate defects with tension readings."),
            ],
            1,
        )

    humidity = machine.get("humidity")
    if humidity is not None and (humidity < 45 or humidity > 75):
        add_candidate(
            "Humidity or environment issue",
            42,
            [_fact("Humidity", humidity), _fact("Defect rate", machine["defect_rate"])],
            ["humidity", "environment"],
            ["No room-level humidity trend or material moisture measurement is available."],
            "The humidity is outside the local nominal band and may affect yarn behavior, but material moisture was not measured.",
            [
                (1, "Measure room humidity at the loom and confirm the material moisture condition."),
                (2, "Check HVAC operation and protect yarn from abrupt environmental changes."),
                (3, "Compare defect and breakage rates across controlled humidity periods."),
            ],
            1,
        )

    candidates.sort(key=lambda item: item["confidence_score"], reverse=True)
    return {
        "success": True,
        "loom_id": machine["loom_id"],
        "analysis_type": "evidence-based root-cause analysis",
        "root_causes": candidates,
        "research_results": research,
        "summary": (
            "No supported root cause was identified from the available evidence."
            if not candidates
            else "Root causes are ranked by evidence-based confidence, not validated probability."
        ),
    }


def root_cause_analysis(loom_id: str) -> dict[str, Any]:
    """Gather the existing evidence tools and run targeted web research."""
    machine = get_machine_status(loom_id)
    if not machine.get("success", False):
        return machine
    maintenance = get_maintenance_history(loom_id)
    diagnosis = diagnose_machine(loom_id)
    queries = build_research_queries(machine, diagnosis)
    research: list[dict[str, Any]] = []
    for query in queries:
        result = web_research(query)
        if result.get("success"):
            research.extend(result.get("results", []))

    analysis = analyze_root_causes(machine, maintenance, diagnosis, research)
    analysis["research_queries"] = queries
    analysis["research_available"] = bool(research)
    if not research:
        analysis["research_note"] = "Web research was unavailable; scores use local evidence only."
    return analysis