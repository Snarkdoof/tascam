# Bug Fixes

## 2026-05-10
- **Import Error in web.py:** Fixed `NameError: name 'Optional' is not defined` by adding `Optional` and `List` to the `typing` imports in `tascam_app/web.py`.
- **Model Discrepancy:** Ensure SQLModel fields like `sa_column=Column(JSON)` are used for complex types (List/Dict) when using SQLite to ensure proper serialization.
