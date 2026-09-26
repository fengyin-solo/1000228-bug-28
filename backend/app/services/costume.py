"""服装造型业务规则：状态流转、字段校验与筛选口径都收在这里。"""
from __future__ import annotations

from typing import Any

from app.store import store

MODULE = "costume"
REQUIRED_FIELDS = ["服装编号", "服装名称", "角色归属"]
OPTIONAL_FIELDS = ["尺码规格", "造型师", "使用场次", "清洗记录"]
STATUS_ORDER = ["待定妆", "已定妆", "使用中", "已归还"]
ACTION_RULES = {"安排定妆": "已定妆", "确认使用": "使用中", "归还服装": "已归还"}
NEGATIVE_ACTIONS = []

# 每个动作只允许从紧邻的前一个状态发起；已经处置过的戏服重复动作直接拦下。
ACTION_SOURCES = {"安排定妆": "待定妆", "确认使用": "已定妆", "归还服装": "使用中"}
DISPLAY_STATUS_FIELD = "当前状态"
SCENE_FIELD = "使用场次"
CLEANING_FIELD = "清洗记录"


def _sync_display(entry: dict[str, Any]) -> dict[str, Any]:
    """列表与详情展示的「当前状态」以内部 status 为准，避免归还后还停在旧状态。"""
    entry[DISPLAY_STATUS_FIELD] = str(entry.get("status") or STATUS_ORDER[0])
    return entry


def _build_cleaning_record(entry: dict[str, Any]) -> str | None:
    """归还时按使用场次生成清洗记录；场次缺失时返回 None，调用方不得改动原戏服资料。"""
    scene = str(entry.get(SCENE_FIELD) or "").strip()
    if not scene:
        return None
    return f"{scene}使用后归还，待清洗"


class CostumeService:
    def list_entries(
        self,
        *,
        keyword: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        rows = store.rows(MODULE)
        if keyword:
            rows = [row for row in rows if keyword in str(row.get("服装编号", ""))]
        if status:
            rows = [row for row in rows if row.get("status") == status]
        total = len(rows)
        start = max(page - 1, 0) * size
        return [_sync_display(row) for row in rows[start:start + size]], total

    def get_entry(self, entry_id: int) -> dict[str, Any] | None:
        entry = store.find(MODULE, entry_id)
        if entry is None:
            return None
        return _sync_display(entry)

    def stats(self) -> list[dict[str, Any]]:
        """按状态统计戏服数量，给列表页的状态卡片做概览与点击筛选。"""
        rows = store.rows(MODULE)
        return [
            {
                "label": f"{status}服装",
                "status": status,
                "value": sum(1 for row in rows if row.get("status") == status),
            }
            for status in STATUS_ORDER
        ]

    def create_entry(self, values: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
        missing = [field for field in REQUIRED_FIELDS if not str(values.get(field) or "").strip()]
        if missing:
            return None, missing
        rows = store.rows(MODULE)
        entry = {"id": max((int(row.get("id", 0)) for row in rows), default=0) + 1}
        entry.update({field: values.get(field) for field in REQUIRED_FIELDS})
        for field in OPTIONAL_FIELDS:
            value = str(values.get(field) or "").strip()
            if value:
                entry[field] = value
        entry["status"] = STATUS_ORDER[0]
        entry["pending"] = True
        entry["abnormal"] = False
        rows.append(entry)
        return _sync_display(entry), []

    def run_action(self, entry_id: int, action: str) -> tuple[dict[str, Any] | None, str]:
        entry = store.find(MODULE, entry_id)
        if entry is None:
            return None, f"戏服 {entry_id} 不存在或已归档"
        if action not in ACTION_RULES:
            return None, f"动作「{action}」不属于服装造型可执行范围"
        target = ACTION_RULES[action]
        if target not in STATUS_ORDER:
            return None, f"目标状态「{target}」不在允许的状态序列里"
        current = str(entry.get("status") or "")
        source = ACTION_SOURCES[action]
        if current != source:
            if current == target:
                return None, f"戏服 {entry_id} 已是「{target}」，重复{action}不再生效"
            return None, f"戏服 {entry_id} 当前状态为「{current or '未知'}」，需先处于「{source}」才能{action}"
        updates: dict[str, Any] = {}
        if action == "归还服装":
            record = _build_cleaning_record(entry)
            if record is None:
                return None, f"戏服 {entry_id} 缺少使用场次，清洗记录生成失败，戏服资料保持原样"
            updates[CLEANING_FIELD] = record
            updates[SCENE_FIELD] = ""
        entry["status"] = target
        entry["pending"] = target != STATUS_ORDER[-1]
        entry["abnormal"] = action in NEGATIVE_ACTIONS
        entry.update(updates)
        return _sync_display(entry), f"戏服已{action}"
