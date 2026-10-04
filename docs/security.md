# Security Direction

These requirements guide future design. The v0.1 simulator has no accounts, networking, economy, trading, or persistent progression yet.

## Trust boundaries

- Treat user-installed and community games as untrusted code and untrusted files.
- Store trusted profiles separately from game installations and save data.
- Games must not directly edit credits, account level, rare items, Voidling progression, or trade ownership.
- Provide a narrow, controlled Void API for reward requests and approved state changes.
- Give games only the files and device capabilities they need. Prefer process isolation and operating-system permissions over voluntary conventions.

## State integrity

- Do not use save-file scrambling or obscurity as a security control.
- Validate the format, range, origin, and authorization of every trusted-state change.
- Add authenticated integrity protection to trusted local records when persistence is introduced.
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

Void credits or tokens are in-device fiction only. They must never be purchasable with real money or redeemable for money, goods, or other real-world value. Any future card or casino-style minigame must remain fictional, non-purchasable, and non-redeemable.
