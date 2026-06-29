"""HCP master data management service."""

import csv
import io
from difflib import SequenceMatcher
from threading import Lock

from cloud.app.schemas.hcp_mdm import HCPImportResult, HCPMaster, HCPProfile, MergeSuggestion, VisitStats

_LOCK = Lock()

_VISIT_HISTORY: dict[str, list[dict]] = {
    "hcp-001": [
        {"date": "2026-06-15", "duration_min": 25, "type": "face-to-face"},
        {"date": "2026-06-10", "duration_min": 15, "type": "phone"},
        {"date": "2026-05-28", "duration_min": 30, "type": "face-to-face"},
    ],
    "hcp-002": [
        {"date": "2026-06-20", "duration_min": 20, "type": "face-to-face"},
        {"date": "2026-06-05", "duration_min": 10, "type": "wechat"},
    ],
}

_HCP_MASTERS: dict[str, HCPMaster] = {
    "hcp-001": HCPMaster(
        master_id="hcp-001",
        primary_name="张伟",
        aliases=["张主任", "张伟医生"],
        hospital="上海市第一人民医院",
        department="心内科",
        title="主任医师",
        specialty="冠脉介入",
        nmpa_id="NMPA-HCP-001",
        phone="13800000001",
        email="zhangwei@example.com",
        unified_score=86.5,
        dedup_status="unique",
        source_systems=["cloud", "assistant", "sales-assistant"],
        prescription_preference={"brand_a": 0.7, "brand_b": 0.3},
        academic_influence=88.5,
        visit_acceptance=0.85,
        channel_preference=["face-to-face", "wechat"],
    ),
    "hcp-001-a": HCPMaster(
        master_id="hcp-001-a",
        primary_name="张伟",
        aliases=["张医生"],
        hospital="上海市第一人民医院",
        department="心血管内科",
        title="主任医师",
        specialty="介入治疗",
        nmpa_id="NMPA-HCP-001",
        phone="13800000001",
        email="zhangwei@example.com",
        unified_score=84.0,
        dedup_status="candidate",
        source_systems=["crm"],
        prescription_preference={"brand_a": 0.6, "brand_c": 0.4},
        academic_influence=85.0,
        visit_acceptance=0.7,
        channel_preference=["face-to-face"],
    ),
    "hcp-002": HCPMaster(
        master_id="hcp-002",
        primary_name="李敏",
        aliases=["李教授"],
        hospital="复旦大学附属中山医院",
        department="神经外科",
        title="副主任医师",
        specialty="神经介入",
        nmpa_id="NMPA-HCP-002",
        phone="13800000002",
        email="limin@example.com",
        unified_score=79.2,
        dedup_status="unique",
        source_systems=["cloud", "assistant"],
        prescription_preference={"brand_b": 0.8, "brand_d": 0.2},
        academic_influence=75.0,
        visit_acceptance=0.6,
        channel_preference=["phone", "wechat"],
    ),
}


def _similar(left: str | None, right: str | None) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


def _match_score(primary: HCPMaster, candidate: HCPMaster) -> float:
    nmpa_score = 1.0 if primary.nmpa_id and primary.nmpa_id == candidate.nmpa_id else 0.0
    phone_score = 1.0 if primary.phone and primary.phone == candidate.phone else 0.0
    name_score = _similar(primary.primary_name, candidate.primary_name)
    hospital_score = _similar(primary.hospital, candidate.hospital)
    department_score = _similar(primary.department, candidate.department)
    return round(
        nmpa_score * 0.35 + phone_score * 0.25 + name_score * 0.2 + hospital_score * 0.15 + department_score * 0.05,
        4,
    )


def resolve_hcp(identifiers: dict[str, str]) -> HCPMaster | None:
    """Resolve an HCP by master_id, nmpa_id, phone, email, or name."""
    for hcp in _HCP_MASTERS.values():
        if identifiers.get("master_id") == hcp.master_id:
            return hcp
        if identifiers.get("nmpa_id") and identifiers["nmpa_id"] == hcp.nmpa_id:
            return hcp
        if identifiers.get("phone") and identifiers["phone"] == hcp.phone:
            return hcp
        if identifiers.get("email") and identifiers["email"] == hcp.email:
            return hcp
        if identifiers.get("name") and identifiers["name"] in [hcp.primary_name, *hcp.aliases]:
            return hcp
    return None


def dedup_check() -> list[MergeSuggestion]:
    suggestions: list[MergeSuggestion] = []
    masters = list(_HCP_MASTERS.values())
    for index, primary in enumerate(masters):
        duplicates: list[str] = []
        best_score = 0.0
        for candidate in masters[index + 1 :]:
            score = _match_score(primary, candidate)
            if score >= 0.82:
                duplicates.append(candidate.master_id)
                best_score = max(best_score, score)
        if duplicates:
            suggestions.append(
                MergeSuggestion(
                    primary_id=primary.master_id,
                    duplicate_ids=duplicates,
                    match_score=best_score,
                )
            )
    return suggestions


def merge_duplicates(primary_id: str, duplicate_ids: list[str]) -> HCPMaster:
    with _LOCK:
        primary = _HCP_MASTERS[primary_id]
        aliases = set(primary.aliases)
        source_systems = set(primary.source_systems)
        for duplicate_id in duplicate_ids:
            duplicate = _HCP_MASTERS.pop(duplicate_id, None)
            if not duplicate:
                continue
            aliases.add(duplicate.primary_name)
            aliases.update(duplicate.aliases)
            source_systems.update(duplicate.source_systems)
        merged = primary.model_copy(
            update={
                "aliases": sorted(aliases),
                "source_systems": sorted(source_systems),
                "dedup_status": "merged",
            }
        )
        _HCP_MASTERS[primary_id] = merged
        return merged


def get_unified_profile(hcp_id: str) -> HCPMaster:
    return _HCP_MASTERS.get(hcp_id) or _HCP_MASTERS["hcp-001"]


def sync_to_end(hcp_id: str | None = None) -> dict[str, int | str]:
    profiles = [get_unified_profile(hcp_id)] if hcp_id else list(_HCP_MASTERS.values())
    return {"status": "synced", "profile_count": len(profiles), "target": "one-cloud-four-ends"}


def get_hcp_profile(hcp_id: str) -> HCPProfile:
    master = get_unified_profile(hcp_id)
    visits = _VISIT_HISTORY.get(hcp_id, [])
    total = len(visits)
    durations = [v["duration_min"] for v in visits]
    avg_duration = round(sum(durations) / len(durations), 1) if durations else 0.0
    last_date = visits[-1]["date"] if visits else None
    if total >= 6:
        freq = "high"
    elif total >= 2:
        freq = "medium"
    else:
        freq = "low"
    stats = VisitStats(
        total_visits=total,
        last_visit_date=last_date,
        visit_frequency=freq,
        avg_visit_duration_min=avg_duration,
    )
    return HCPProfile(master=master, visit_stats=stats)


_NEXT_ID = 100


def _next_id() -> str:
    global _NEXT_ID
    with _LOCK:
        _NEXT_ID += 1
        return f"hcp-import-{_NEXT_ID}"


def import_hcp_csv(csv_content: str) -> HCPImportResult:
    reader = csv.DictReader(io.StringIO(csv_content))
    result = HCPImportResult()
    for row in reader:
        try:
            master_id = row.get("master_id") or _next_id()
            master = HCPMaster(
                master_id=master_id,
                primary_name=row["primary_name"],
                aliases=[a.strip() for a in row.get("aliases", "").split(";") if a.strip()],
                hospital=row["hospital"],
                department=row.get("department", ""),
                title=row.get("title", ""),
                specialty=row.get("specialty", ""),
                nmpa_id=row.get("nmpa_id") or None,
                phone=row.get("phone") or None,
                email=row.get("email") or None,
                unified_score=float(row.get("unified_score", 0)),
                dedup_status=row.get("dedup_status", "imported"),
                source_systems=[s.strip() for s in row.get("source_systems", "cloud").split(";") if s.strip()],
                academic_influence=float(row.get("academic_influence", 0)),
                visit_acceptance=float(row.get("visit_acceptance", 0)),
                channel_preference=[c.strip() for c in row.get("channel_preference", "").split(";") if c.strip()],
            )
            with _LOCK:
                _HCP_MASTERS[master_id] = master
            result.imported += 1
        except Exception as exc:
            result.errors.append(f"Row {result.imported + result.skipped + len(result.errors) + 1}: {exc}")
            result.skipped += 1
    return result
