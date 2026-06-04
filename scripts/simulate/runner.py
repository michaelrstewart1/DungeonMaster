"""CLI entry point: `python -m scripts.simulate.runner --scenario smoke`.

Boots N `BotPlayer`s, drives them through a scenario, writes a transcript.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

from .api_client import ApiClient
from .bot_player import BotPlayer, TranscriptEntry, TurnOwner

logger = logging.getLogger("simulate.runner")


def _ws_url_from(base_url: str) -> str:
    if base_url.startswith("http://"):
        return "ws://" + base_url[len("http://") :]
    if base_url.startswith("https://"):
        return "wss://" + base_url[len("https://") :]
    return base_url


async def run_scenario(
    scenario_name: str,
    *,
    base_url: str,
    output_dir: Path,
    max_turns: int,
    wall_clock_timeout: float = 120.0,
) -> dict:
    """Load a scenario module and execute it."""
    module = importlib.import_module(f"scripts.simulate.scenarios.{scenario_name}")
    if not hasattr(module, "build"):
        raise RuntimeError(
            f"scenario module {scenario_name!r} must define a `build()` function"
        )

    transcript: list[TranscriptEntry] = []
    ws_url = _ws_url_from(base_url)

    async with ApiClient(base_url=base_url) as api:
        if not await api.health():
            raise RuntimeError(
                f"Backend at {base_url} is not reachable (GET /api/health failed)"
            )

        ctx = await module.build(api)
        bot_configs = ctx["bots"]
        session_id = ctx["session_id"]
        room_code = ctx["room_code"]
        expected_phases = ctx.get("expected_phases", [])

        bots: list[BotPlayer] = []
        for cfg in bot_configs:
            bots.append(
                BotPlayer(
                    config=cfg,
                    api=api,
                    ws_base_url=ws_url,
                    transcript=transcript,
                )
            )

        turn_owner = TurnOwner(bots)
        for bot in bots:
            bot.turn_owner = turn_owner

        for bot in bots:
            await bot.join(room_code)
        for bot in bots:
            await bot.connect()
        for bot in bots:
            await bot.announce()

        # Brief pause so player_update broadcasts settle before the first action.
        await asyncio.sleep(0.2)

        # Optional scenario hook: run setup that needs both bots connected
        # but should NOT count as a bot turn (e.g. seeding state via REST,
        # driving an out-of-band protocol like trade).
        post_setup = ctx.get("post_setup")
        if post_setup is not None:
            try:
                await post_setup(api, ctx, bots)
            except Exception as exc:
                logger.exception("post_setup hook failed: %s", exc)

        await bots[0].take_initial_turn()

        tasks = [
            asyncio.create_task(bot.run(max_turns=max_turns), name=f"bot-{bot.config.name}")
            for bot in bots
        ]
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=wall_clock_timeout,
            )
        except asyncio.TimeoutError:
            logger.warning("scenario exceeded %.0fs wall-clock; cancelling bots", wall_clock_timeout)
            for t in tasks:
                t.cancel()

        for bot in bots:
            await bot.close()

        result = {
            "scenario": scenario_name,
            "session_id": session_id,
            "room_code": room_code,
            "base_url": base_url,
            "bots": [bot.config.name for bot in bots],
            "expected_phases": expected_phases,
            "transcript_length": len(transcript),
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = output_dir / "transcript.jsonl"
    with transcript_path.open("w", encoding="utf-8") as fh:
        for entry in transcript:
            fh.write(json.dumps(entry.to_jsonable()) + "\n")
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    if hasattr(module, "assertions"):
        problems = module.assertions(transcript, result)
        if problems:
            result["assertion_failures"] = problems
            (output_dir / "assertion_failures.json").write_text(
                json.dumps(problems, indent=2), encoding="utf-8"
            )

    return result


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run a DungeonMaster bot scenario.")
    parser.add_argument("--scenario", default="smoke")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--max-turns", type=int, default=20)
    parser.add_argument("--runs-dir", default="runs")
    parser.add_argument("--timeout", type=float, default=120.0, help="Wall-clock cap in seconds")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
    )

    run_id = time.strftime("%Y%m%dT%H%M%S")
    output_dir = Path(args.runs_dir) / f"{args.scenario}-{run_id}"

    try:
        result = asyncio.run(
            run_scenario(
                args.scenario,
                base_url=args.base_url,
                output_dir=output_dir,
                max_turns=args.max_turns,
                wall_clock_timeout=args.timeout,
            )
        )
    except Exception as exc:
        logger.exception("scenario failed: %s", exc)
        return 1

    failures = result.get("assertion_failures") or []
    logger.info(
        "scenario %s: %d transcript entries, %d assertion failures, output in %s",
        args.scenario,
        result.get("transcript_length", 0),
        len(failures),
        output_dir,
    )
    if failures:
        for f in failures:
            logger.error("ASSERT FAIL: %s", f)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
