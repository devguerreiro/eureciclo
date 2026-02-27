from bisect import bisect_left


def answer(capacity, bottles):
    SCALE = 10  # 0.1 precision scaling
    target = int(round(capacity * SCALE))
    items = [int(round(b * SCALE)) for b in bottles]

    n = len(items)
    mid = n // 2
    left_part = items[:mid]
    right_part = items[mid:]

    # ---------- GENERATE SUBSETS WITH MASK ----------
    def generate_subsets(arr):
        m = len(arr)
        subsets = []
        for mask in range(1 << m):
            total = 0
            count = 0
            for i in range(m):
                if mask & (1 << i):
                    total += arr[i]
                    count += 1
            subsets.append((total, count, mask))
        return subsets

    left_subsets = generate_subsets(left_part)
    right_subsets = generate_subsets(right_part)

    # ---------- PARETO PRUNING (REMOVE DOMINATED STATES) ----------
    right_subsets.sort()  # sort by total ascending

    filtered = []
    min_count = float("inf")

    # Traverse backwards to keep only Pareto optimal states
    for total, count, mask in reversed(right_subsets):
        if count < min_count:
            filtered.append((total, count, mask))
            min_count = count

    right_subsets = list(reversed(filtered))
    right_totals = [t for t, _, _ in right_subsets]

    # ---------- OPTIMAL SEARCH ----------
    best_total = float("inf")
    best_count = float("inf")
    best_masks = None

    for total_left, count_left, mask_left in left_subsets:
        needed = target - total_left
        if needed < 0:
            needed = 0

        idx = bisect_left(right_totals, needed)

        if idx < len(right_subsets):
            total_right, count_right, mask_right = right_subsets[idx]
            combined_total = total_left + total_right
            combined_count = count_left + count_right

            if combined_total >= target:
                if combined_total < best_total or (
                    combined_total == best_total and combined_count < best_count
                ):
                    best_total = combined_total
                    best_count = combined_count
                    best_masks = (mask_left, mask_right)

    if best_masks is None:
        return None, "Insufficient volume"

    # ---------- FAST RECONSTRUCTION ----------
    result = []
    mask_left, mask_right = best_masks

    for i in range(len(left_part)):
        if mask_left & (1 << i):
            result.append(left_part[i])

    for i in range(len(right_part)):
        if mask_right & (1 << i):
            result.append(right_part[i])

    result_final = [round(v / SCALE, 2) for v in result]
    overflow = round((best_total - target) / SCALE, 2)

    return result_final, overflow


# =========================
# Example Tests
# =========================

if __name__ == "__main__":
    test_cases = [
        (7, [1, 3, 4.5, 1.5, 3.5]),
        (5, [1, 3, 4.5, 1.5]),
        (4.9, [4.5, 0.4]),
    ]

    for capacity, bottles in test_cases:
        selected, overflow = answer(capacity, bottles)
        print(f"Capacity: {capacity}L")
        print(f"Selected bottles: {selected}")
        print(f"Overflow: {overflow}L")
        print("-" * 40)
