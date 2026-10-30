# WinKit follow-up roadmap

The following modules were discussed as useful extensions but are not part of the current 2.0 implementation yet. They need separate design and Windows testing before being advertised as stable features.

1. Clipboard history manager (explicit opt-in, local storage, clear controls, sensitive-text exclusions).
2. Display profiles for multiple monitors (save/restore screen topology and resolution safely).
3. Context-menu editor (export exact registry keys before any change, per-entry restore, Windows-version checks).
4. Automation scheduler (visible task definitions, user approval, pause/disable controls, activity log).
5. Duplicate-file finder (hash-based preview only first; deletion only after a separate review workflow).
6. Process and startup manager with publisher/path details and conservative controls.
7. Additional diagnostic packs for audio, Bluetooth and Windows Update.
8. Optional GPU telemetry adapters for supported vendor drivers; generic GPU temperature is not available on every PC.

The current release intentionally avoids bulk service disabling, blanket registry cleaners, security-feature toggles, and one-click driver deletion.
