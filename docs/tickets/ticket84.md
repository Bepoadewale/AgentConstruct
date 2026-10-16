# Ticket 84: Stabilize invitation token contract test

## Goal

Remove a probabilistic test failure caused by rejecting a valid URL-safe token prefix.

## Scope

- Assert the documented security properties of invitation tokens.
- Repeat the assertion enough times to cover token variability.
- Run the backend verification and CI gates.

## Status

In progress.
