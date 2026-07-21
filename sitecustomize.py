"""Apply UMML's Linux detection compatibility layers for source launches."""

try:
    from umml_detection_hotfix import apply as apply_detection_hotfix
    from umml_manual_location_fix import apply as apply_manual_location_fix

    apply_detection_hotfix()
    apply_manual_location_fix()
except Exception as exc:  # Keep Python startup usable and surface details later.
    print(f"UMML detection compatibility could not be applied: {exc}")
