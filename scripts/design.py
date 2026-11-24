"""Reproducible option counterbalancing for future collections.

Two of the four conditions have correct=A in each repeat of each question.
The assignment reverses in the next repeat. Thus each two-repeat cell is
balanced, and repeat-based validation contains both answer positions.
Existing evaluation logs retain their recorded historical assignments.
"""
import hashlib
import random


def correct_is_a(qid, condition, rep, conditions, seed):
    digest = hashlib.sha256(f"{seed}:{qid}:option-order-v2".encode()).digest()
    rng = random.Random(int.from_bytes(digest[:8], "big"))
    order = list(conditions)
    rng.shuffle(order)
    return (condition in order[: len(order) // 2]) != bool(rep % 2)
