#!/usr/bin/env python3
#
# driver.py - The driver tests the correctness of the student's cache
#     simulator and the correctness and performance of their transpose
#     function. It uses ./test-csim to check the correctness of the
#     simulator and it runs ./test-trans on three different sized
#     matrices (32x32, 64x64, and 61x67) to test the correctness and
#     performance of the transpose function.
#
import subprocess
import re
import sys
import argparse


def computeMissScore(miss: int, lower: int, upper: int, full_score: int) -> float:
    """
    Compute the score depending on the number of cache misses.
    """
    if miss <= lower:
        return float(full_score)
    if miss >= upper:
        return 0.0

    score = (miss - lower) * 1.0
    miss_range = (upper - lower) * 1.0
    return round((1.0 - score / miss_range) * full_score, 1)


def run_cmd_capture(cmd: str) -> str:
    """
    Run a shell command and return stdout as text (UTF-8), with replacement for decode errors.
    """
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out_bytes = p.communicate()[0] or b""
    return out_bytes.decode("utf-8", errors="replace")


def main() -> int:
    # Configure maxscores here
    maxscore = {
        "csim": 27,
        "transc": 1,   # kept for parity with original, though unused in scoring
        "trans32": 8,
        "trans64": 8,
        "trans61": 10,
    }

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-A",
        action="store_true",
        dest="autograde",
        help="emit autoresult string for Autolab",
    )
    args = parser.parse_args()
    autograde = args.autograde

    # Check the correctness of the cache simulator
    print("Part A: Testing cache simulator")
    print("Running ./test-csim")
    out = run_cmd_capture("./test-csim")

    resultsim = None
    for line in out.splitlines():
        if re.match(r"TEST_CSIM_RESULTS", line):
            resultsim = re.findall(r"(\d+)", line)
        else:
            print(f"{line}")

    if not resultsim:
        print("ERROR: Could not find TEST_CSIM_RESULTS in ./test-csim output.", file=sys.stderr)
        return 1

    # Check the correctness and performance of the transpose function
    print("Part B: Testing transpose function")

    def run_trans(M: int, N: int):
        print(f"Running ./test-trans -M {M} -N {N}")
        out_local = run_cmd_capture(f"./test-trans -M {M} -N {N} | grep TEST_TRANS_RESULTS")
        return re.findall(r"(\d+)", out_local)

    result32 = run_trans(32, 32)
    result64 = run_trans(64, 64)
    result61 = run_trans(61, 67)

    # Validate expected fields: [correctness_flag, miss_count, ...]
    for name, res in [("32x32", result32), ("64x64", result64), ("61x67", result61)]:
        if len(res) < 2:
            print(f"ERROR: Could not parse TEST_TRANS_RESULTS for {name}.", file=sys.stderr)
            return 1

    # Compute the scores for each step
    csim_cscore = list(map(int, resultsim[0:1]))  # preserve original behavior
    trans_cscore = int(result32[0]) * int(result64[0]) * int(result61[0])  # kept for parity (unused)

    miss32 = int(result32[1])
    miss64 = int(result64[1])
    miss61 = int(result61[1])

    trans32_score = computeMissScore(miss32, 300, 600, maxscore["trans32"]) * int(result32[0])
    trans64_score = computeMissScore(miss64, 1300, 2000, maxscore["trans64"]) * int(result64[0])
    trans61_score = computeMissScore(miss61, 2000, 3000, maxscore["trans61"]) * int(result61[0])

    total_score = csim_cscore[0] + trans32_score + trans64_score + trans61_score

    # Summarize the results
    print("\nCache Lab summary:")
    print(f"{'':-<44}".replace("-", ""))  # no-op visual parity; safe to remove
    print("%-22s%8s%10s%12s" % ("", "Points", "Max pts", "Misses"))
    print("%-22s%8.1f%10d" % ("Csim correctness", csim_cscore[0], maxscore["csim"]))

    misses = str(miss32)
    if miss32 == 2**31 - 1:
        misses = "invalid"
    print("%-22s%8.1f%10d%12s" % ("Trans perf 32x32", trans32_score, maxscore["trans32"], misses))

    misses = str(miss64)
    if miss64 == 2**31 - 1:
        misses = "invalid"
    print("%-22s%8.1f%10d%12s" % ("Trans perf 64x64", trans64_score, maxscore["trans64"], misses))

    misses = str(miss61)
    if miss61 == 2**31 - 1:
        misses = "invalid"
    print("%-22s%8.1f%10d%12s" % ("Trans perf 61x67", trans61_score, maxscore["trans61"], misses))

    print(
        "%22s%8.1f%10d"
        % (
            "Total points",
            total_score,
            maxscore["csim"] + maxscore["trans32"] + maxscore["trans64"] + maxscore["trans61"],
        )
    )

    # Emit autoresult string for Autolab if called with -A option
    if autograde:
        autoresult = "%.1f:%d:%d:%d" % (total_score, miss32, miss64, miss61)
        print(f"\nAUTORESULT_STRING={autoresult}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

