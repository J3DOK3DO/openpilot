#!/usr/bin/env python3
"""Pinned MVL vs Dom Accord11G literal tuning audit. No car APIs, imports or CAN."""
import argparse
import ast
import json
import subprocess
from pathlib import Path

MVL_OPENDDBC_PIN = "66a3ea89f42890a99237dbf20789f1ea3d3d5611"
MVL_OPENPILOT_PIN = "48211d6a633cd172a8a8de7bc33004f3bc5f02a0"
DOM_C13_PIN = "966ffe5d175d59b3ce681249841aa0b3abfae443"
BUILT_PIN = "586da6b91ffb43e2a1e114072104b694d3c8a2b3"
FIELDS = ("steerActuatorDelay", "kpV", "kiV", "kf")


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True, stderr=subprocess.PIPE).strip()


def is_target(node):
    return (isinstance(node, ast.Compare) and len(node.ops) == 1
            and isinstance(node.ops[0], ast.Eq)
            and isinstance(node.left, ast.Name) and node.left.id == "candidate"
            and len(node.comparators) == 1
            and isinstance(node.comparators[0], ast.Attribute)
            and node.comparators[0].attr == "HONDA_ACCORD_11G"
            and isinstance(node.comparators[0].value, ast.Name)
            and node.comparators[0].value.id == "CAR")


def extract_profile(source):
    """Parse literal-only assignments; never execute vehicle code."""
    found_profiles = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.If) or not is_target(node.test):
            continue
        found = {}
        for statement in node.body:
            if not isinstance(statement, ast.Assign):
                continue
            try:
                value = ast.literal_eval(statement.value)
            except (ValueError, TypeError, SyntaxError, RecursionError):
                continue
            for target in statement.targets:
                targets = target.elts if isinstance(target, ast.Tuple) else [target]
                values = value if isinstance(target, ast.Tuple) else [value]
                for part, val in zip(targets, values):
                    key = part.attr if isinstance(part, ast.Attribute) else ""
                    if key not in FIELDS:
                        continue
                    if isinstance(val, (tuple, list)) and len(val) == 1:
                        val = val[0]
                    if isinstance(val, (int, float)) and not isinstance(val, bool):
                        found[key] = float(val)
        if len(found) == len(FIELDS):
            found_profiles.append(found)
    if len(found_profiles) != 1:
        raise ValueError(f"Expected one complete Accord11G profile; found {len(found_profiles)}")
    return found_profiles[0]


def compare(dom_source, mvl_source):
    dom, mvl = extract_profile(dom_source), extract_profile(mvl_source)
    differences = {k: dom[k] - mvl[k] for k in FIELDS}
    return {"dom": dom, "mvl": mvl, "differences": differences,
            "same_four_numeric_values": all(x == 0.0 for x in differences.values())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dom", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--mvl", type=Path, default=Path("/mnt/commadrive/_mvl_opendbc_sp_honda_dev_202608_review"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    dom, mvl = args.dom.resolve(), args.mvl.resolve()
    head = git(dom, "rev-parse", "HEAD")
    if head != DOM_C13_PIN:
        git(dom, "merge-base", "--is-ancestor", DOM_C13_PIN, "HEAD")
    dom_path = "opendbc_repo/opendbc/car/honda/interface.py"
    dom_source = git(dom, "show", f"{DOM_C13_PIN}:{dom_path}")
    mvl_source = git(mvl, "show", f"{MVL_OPENDDBC_PIN}:opendbc/car/honda/interface.py")
    result = compare(dom_source, mvl_source)
    result.update({"kind": "READ_ONLY_SOURCE_AUDIT_NOT_VEHICLE_TUNING",
                   "dom_c13": DOM_C13_PIN, "built_control_source": BUILT_PIN,
                   "mvl_openpilot": MVL_OPENPILOT_PIN, "mvl_opendbc": MVL_OPENDDBC_PIN,
                   "unchanged_against_c13": (dom/dom_path).read_text().strip() == dom_source.strip(),
                   "vehicle_qualified": False, "installable": False,
                   "alpha_long_ported": False, "full_mvl_customizations_ported": False})
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output)
    else:
        print(output)
    if not result["same_four_numeric_values"] or not result["unchanged_against_c13"]:
        raise SystemExit("PIN_PARITY_FAIL: Unexpected source or numeric discrepancy")
    print("PIN_PARITY_PASS: 4 static values identical. No physical driving claim.")


if __name__ == "__main__":
    main()
