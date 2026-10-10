# Challenge 2 v2 — Constrained Average

## Candidate-facing task

Implement this function:

```python
calculate_constrained_average_v2(numbers, minimum, maximum)
```

The function accepts an iterable of values and inclusive numeric bounds.

Apply these rules in order:

1. **Validate the bounds.**
   - `minimum` and `maximum` must be real numbers (`int` or `float`), but not booleans. Otherwise raise `TypeError`.
   - If either bound is NaN, or `minimum > maximum`, raise `ValueError`.
2. **Validate every input element.**
   - `numbers` may be any iterable.
   - Every element must be a real number, but not a boolean. Otherwise raise `TypeError`, even if that element would later be filtered out.
   - NaN elements are valid numeric elements.
3. **Filter inclusively.** Keep values satisfying `minimum <= value <= maximum`. NaN values are dropped by these comparisons.
4. **Remove consecutive duplicates from the filtered sequence.** Preserve order. Values such as `1` and `1.0` compare equal. Non-consecutive repeats remain.
5. **Trim outliers once.** Calculate the mean and population standard deviation of the deduplicated sequence. Remove every value whose absolute distance from the mean is strictly greater than two population standard deviations. Do not deduplicate again after trimming.
6. Return the arithmetic mean of the remaining values as a float. Return `None` if filtering leaves no values.

The intended complexity is linear in the input size. The reference implementation and regression tests in this repository are for maintainers; they should not be distributed as hidden evaluation materials to candidates.

## Benchmark validation

The local test suite includes edge cases, invalid inputs, a million-item performance check, a deterministic randomized oracle check, and mutation checks for common incorrect implementations.

Performance thresholds can vary by machine; measure them in the target evaluation environment before using them as strict grading limits.
