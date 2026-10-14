# AgentConstruct UI design system

This document is the implementation contract for the local web product. It is intentionally practical: the product should feel calm, trustworthy, and operationally clear rather than like an AI novelty surface.

## Foundations

- **Color:** ink, muted text, neutral canvas, blue action, green success, and red failure tokens are defined in `apps/web/styles.css`.
- **Typography:** system UI fonts for product text and monospace for digests, commands, and structured evidence.
- **Spacing:** 4px base rhythm with 8px, 12px, 16px, 24px, 32px, and 48px compositions.
- **Surfaces:** white cards on a neutral canvas, 1px borders, restrained shadows, and no gradients or decorative AI imagery.
- **Hierarchy:** outcome first, then selected architecture, then cost/security/observability evidence, then governance actions.

## Components

- Primary and secondary buttons have explicit hover, focus, disabled, and busy states.
- Inputs use visible labels, 44px minimum touch height, and keyboard focus rings.
- Status chips communicate lifecycle state without relying on color alone.
- Cards group one decision or evidence domain; raw data is reserved for inspectable technical detail.
- Empty and loading states explain what is missing and what the user can do next.
- Mobile navigation exposes the same core destinations as desktop navigation.

## Accessibility contract

- Keyboard users can reach every action and see a 3px focus indicator.
- Dynamic workflow messages and audit updates use polite live regions.
- Touch targets are at least 44px on mobile.
- Reduced-motion preferences disable non-essential movement.
- Forced-colors mode keeps borders and controls visible.
- The UI does not use color as the only signal for plan status.

## Product boundaries

The UI presents one recommended AWS plan and makes the approval/deployment boundary explicit. Approval is not deployment. Local/demo mode is labeled. Cloud mutation is never triggered by presentation code.

## QA checklist

1. Check desktop, tablet, and narrow mobile widths.
2. Navigate with keyboard only, including command palette and mobile menu.
3. Confirm busy, failure, empty, and success states are understandable.
4. Confirm no gradient declarations or decorative AI effects are introduced.
5. Run `make browser-contract`, `make customer-plan-e2e`, `make lint`, and `make test`.
