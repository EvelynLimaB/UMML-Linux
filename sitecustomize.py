"""Apply UMML's Linux Steam/Proton autodetection engine for source launches."""

try:
    from umml_autodetect import apply

    apply()
except Exception as exc:  # Keep Python startup usable and expose details to logs.
    print(f"UMML autodetection could not be applied: {exc}")
