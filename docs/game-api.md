# Void Community Game API — Design Contract

Status: design only. Void Flip v0.3 does not execute community packages.

## Manifest

A future package declares a stable game ID, title, author, package version, minimum API version, entry point, supported player count, display usage, requested permissions, and storage quota. Unknown fields and unsupported API versions must fail closed.

## Launch context

The platform may provide opaque session ID, locale, accessibility settings, logical display dimensions, and a package-owned save directory. It must not provide a trusted-profile path or device credentials.

## Input and display

Games receive named actions (`UP`, `DOWN`, `LEFT`, `RIGHT`, `A`, `B`, `X`, `Y`, `START`, `SELECT`, `HOME`, `BACK`) through a platform channel. Display access is limited to approved top/bottom logical surfaces; direct framebuffer or window ownership is not part of the contract.

## Storage

Each package receives an isolated, quota-limited directory. It receives no direct access to another game's data, the trusted profile, Flux, items, mastery, progression, or credentials.

## Reward requests

A game may submit a bounded `RewardRequest` containing its game ID, opaque session ID, declared result metrics, and one-time result ID. Trusted platform code validates the request and determines the actual reward. A game never writes Flux, XP, bond, inventory, mastery, quests, achievements, or ownership directly.

## Permissions

Permissions must be explicit, minimal, user-visible, and revocable. Network, microphone, peer discovery, and external files are denied by default. API versioning and permission changes require compatibility checks.

## Trust boundary

Community packages are untrusted. A production implementation requires process isolation, operating-system restrictions, resource/time limits, strict message parsing, crash containment, and package trust labels. Obfuscation is not a security control.
