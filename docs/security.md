# Security Direction

These requirements guide current and future design. v0.2 has local persistence and a fictional Flux economy, but still has no accounts, networking, or active trading.

## Trust boundaries

- Treat user-installed and community games as untrusted code and untrusted files.
- Store trusted profiles separately from game installations and save data.
- Games must not directly edit credits, account level, rare items, Voidling progression, or trade ownership.
- Provide a narrow, controlled Void API for reward requests and approved state changes.
- Give games only the files and device capabilities they need. Prefer process isolation and operating-system permissions over voluntary conventions.

## State integrity

- Do not use save-file scrambling or obscurity as a security control.
- Validate the format, range, origin, and authorization of every trusted-state change.
- The current JSON profile is a local single-player save, not a tamper-proof authority. Add authenticated integrity protection before shared ownership, trading, or competitive rewards exist.
- Built-in games submit bounded result records to `CoreLoop`; they do not directly award Flux or mutate trusted inventory.
- Applied game and quest rewards retain rolling IDs so reopening a result screen cannot duplicate a payout.
- Keep recovery-safe backups and schema versions so interrupted writes and upgrades do not corrupt a profile.
- Use Node or another authoritative service to validate multiplayer results, trades, and ownership when those features require shared trust.
- Design trading as an atomic transfer: it must either complete for both parties or complete for neither.

## Network direction

- Authenticate devices and peers before granting privileged operations.
- Encrypt network traffic that contains identity, profile, trade, or private session data.
- Treat all peer and Node messages as untrusted input; apply size limits, timeouts, replay protection, and strict parsing.
- Allow users to remove paired devices and revoke credentials.

## Community content

- Define a package manifest, permissions, size limits, and compatible API version.
- Never grant a game raw credentials or unrestricted access to system services.
- Keep platform updates and trusted code outside community-writable locations.
- Plan for signed official packages while clearly labeling unsigned community software.

## Fictional currency

Flux and all future Void currencies are in-device fiction only. They must never be purchasable with real money or redeemable for money, goods, or other real-world value. Any future card or casino-style minigame must remain fictional, non-purchasable, and non-redeemable.
