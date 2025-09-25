#!/usr/bin/env python3
"""
Example: Detecting logical fallacies in text.

This example demonstrates the logical_fallacies detector,
which flags potential logical fallacies like ad populum or false dichotomy.
"""

from hallucination_detector import detect_text

# Example texts with potential fallacies
examples = [
    "Everyone knows that the sky is blue.",  # Ad populum
    "Either you support this or you're against progress.",  # False dichotomy
    "You can't trust him because he's a politician.",  # Ad hominem
    "Obviously, this is the best solution.",  # Appeal to obviousness
    "This claim is clearly true.",  # Overlaps with overconfidence
]

for text in examples:
    result = detect_text(text, skip_json=True)
    print(f"Text: {text}")
    print(f"OK: {result.ok}, Reasons: {result.reasons}, Severity: {result.severity}")
    print()