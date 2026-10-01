from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import unittest

import pandas as pd

from central_logic import TZ, phase_view_state, process_source, sort_audit_queue


def date_days_ago(days: int) -> str:
    return (datetime.now(TZ).date() - timedelta(days=days)).strftime("%d/%m/%Y")


class ProcessSourcePhaseScopeTests(unittest.TestCase):
    def test_file_with_multiple_phases_keeps_only_selected_phase(self):
        source = pd.DataFrame(
            {
                "ID": ["EQ-1", "QUAL-1"],
                "Fase": ["EM QUALIFICAÇÃO", "QUALIFICADO"],
                "Data da mudança de etapa": [date_days_ago(2), "data inválida"],
            }
        )

        result = process_source(source, "EM QUALIFICAÇÃO")

        self.assertEqual(result["ID"].tolist(), ["EQ-1"])

    def test_duplicate_ids_outside_target_phase_do_not_invalidate_import(self):
        source = pd.DataFrame(
            {
                "ID": ["EQ-1", "DUP", "DUP"],
                "Fase": ["EM QUALIFICAÇÃO", "QUALIFICADO", "QUALIFICADO"],
                "Data da mudança de etapa": [
                    date_days_ago(1),
                    date_days_ago(4),
                    date_days_ago(5),
                ],
            }
        )

        result = process_source(source, "EM QUALIFICAÇÃO")

        self.assertEqual(result["ID"].tolist(), ["EQ-1"])

    def test_duplicate_ids_inside_target_phase_are_rejected(self):
        source = pd.DataFrame(
            {
                "ID": ["DUP", "DUP"],
                "Fase": ["EM QUALIFICAÇÃO", "EM QUALIFICAÇÃO"],
                "Data da mudança de etapa": [date_days_ago(1), date_days_ago(2)],
            }
        )

        with self.assertRaisesRegex(ValueError, "duplicados"):
            process_source(source, "EM QUALIFICAÇÃO")


class AuditQueueOrderTests(unittest.TestCase):
    def make_current(self, rows: list[tuple[str, int, int]]) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "ID": identifier,
                    "aging_dias": aging,
                    "ordem_prioridade": priority,
                    "data_entrada_fase": f"2026-09-{30 - aging:02d} 00:00:00",
                }
                for identifier, aging, priority in rows
            ]
        )

    def test_elevados_orders_six_days_before_seven_days(self):
        elevated = self.make_current([("7d", 7, 5), ("6d", 6, 3)])

        result = sort_audit_queue(elevated)

        self.assertEqual(result["ID"].tolist(), ["6d", "7d"])

    def test_inside_sla_orders_two_then_one_then_zero_days(self):
        inside = self.make_current([("0d", 0, 7), ("1d", 1, 2), ("2d", 2, 1)])

        result = sort_audit_queue(inside)

        self.assertEqual(result["ID"].tolist(), ["2d", "1d", "0d"])


class PhaseViewStateTests(unittest.TestCase):
    def test_empty_state_and_backend_error_are_distinct(self):
        empty = pd.DataFrame()

        self.assertEqual(phase_view_state(empty, None), "empty")
        self.assertEqual(
            phase_view_state(empty, "backend indisponível"),
            "backend_error",
        )
        self.assertEqual(
            phase_view_state(pd.DataFrame([{"ID": "1"}]), None),
            "ready",
        )


class AppsScriptRepositoryContractTests(unittest.TestCase):
    def test_versioned_backend_contains_required_contract(self):
        code = (
            Path(__file__).parents[1] / "apps-script" / "Code.gs"
        ).read_text(encoding="utf-8")

        for required in (
            'current: "eq_current"',
            'history: "eq_history"',
            'meta: "eq_meta"',
            'current: "qual_current"',
            'history: "qual_history"',
            'meta: "qual_meta"',
            "function migrateLegacyEq_",
            "function loadPhase_",
            "function savePhase_",
            "function upsertDailyHistory_",
        ):
            self.assertIn(required, code)


if __name__ == "__main__":
    unittest.main()
