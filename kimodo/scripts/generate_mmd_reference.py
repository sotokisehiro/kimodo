# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Generate the reference PMX model used to validate Kimodo VMD exports."""

from __future__ import annotations

import argparse

from kimodo.assets import ASSETS_ROOT
from kimodo.exports.pmx import save_reference_pmx


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the Kimodo MMD reference PMX mannequin.")
    parser.add_argument(
        "output",
        nargs="?",
        default=str(ASSETS_ROOT / "mmd" / "kimodo_reference.pmx"),
        help="Output PMX path (default: packaged MMD asset path).",
    )
    args = parser.parse_args(argv)
    save_reference_pmx(args.output)
    print(f"Saved Kimodo MMD reference model to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
