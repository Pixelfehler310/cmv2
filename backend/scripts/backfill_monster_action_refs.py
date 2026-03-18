from __future__ import annotations

import argparse
import asyncio
from typing import Any

from sqlalchemy import select

from src.data.lib.monster import Monster
from src.data.lib.monster_action_refs import normalize_monster_actions
from src.database import AsyncSessionLocal


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Backfill monster.actions payloads from legacy mechanics entries "
            "to strict canonical action references."
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist changes to the database. Without this flag the script runs in dry-run mode.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional max number of monsters to process (0 means all).",
    )
    return parser


async def backfill_monster_action_refs(apply: bool = False, limit: int = 0) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "apply": apply,
        "processed": 0,
        "changed": 0,
        "unchanged": 0,
        "examples": [],
    }

    async with AsyncSessionLocal() as session:
        stmt = select(Monster).order_by(Monster.name.asc())
        result = await session.execute(stmt)
        monsters = list(result.scalars().all())
        if limit > 0:
            monsters = monsters[:limit]

        for monster in monsters:
            summary["processed"] += 1
            existing_actions = monster.actions if isinstance(
                monster.actions, list) else []
            normalized_actions = normalize_monster_actions(
                monster.name, existing_actions)

            if normalized_actions != existing_actions:
                summary["changed"] += 1
                if len(summary["examples"]) < 10:
                    summary["examples"].append(
                        {
                            "monster": monster.name,
                            "before": existing_actions,
                            "after": normalized_actions,
                        }
                    )
                if apply:
                    monster.actions = normalized_actions
            else:
                summary["unchanged"] += 1

        if apply:
            await session.commit()
        else:
            await session.rollback()

    return summary


async def _main_async(args: argparse.Namespace) -> int:
    summary = await backfill_monster_action_refs(apply=args.apply, limit=max(args.limit, 0))

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[backfill_monster_action_refs] mode={mode}")
    print(
        "processed={processed} changed={changed} unchanged={unchanged}".format(
            processed=summary["processed"],
            changed=summary["changed"],
            unchanged=summary["unchanged"],
        )
    )
    if summary["examples"]:
        print("sample_changes=")
        for example in summary["examples"]:
            print(f"- monster={example['monster']}")
            print(f"  before={example['before']}")
            print(f"  after={example['after']}")

    return 0


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    return asyncio.run(_main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
