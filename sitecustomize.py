"""Apply UMML's Linux detection compatibility layer for source launches."""

try:
    from umml_detection_hotfix import apply

    apply()
except Exception as exc:  # Keep Python startup usable and surface details later.
    print(f"UMML detection hotfix could not be applied: {exc}")
