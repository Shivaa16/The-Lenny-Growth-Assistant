# Product Design

## Principles

- Evidence before eloquence: sources remain visible and understandable.
- Progressive complexity: ordinary users see a simple chat; provider and retrieval details remain inspectable.
- Artifacts are first-class: generated work opens beside the conversation and can be reviewed without leaving the product.
- Failure is a product state: unavailable models, empty evidence, and timeouts receive clear recovery guidance.
- Calm density: prioritize readable research and writing over dashboard decoration.

## Visual system

The visual language is deliberately closer to a professional research tool than an AI showcase. A near-white slate canvas and white content surfaces reduce fatigue, navy navigation establishes hierarchy, and a single medium-blue accent identifies interactive and evidence-related elements. Decorative gradients, glow effects, and unnecessary texture are excluded. Borders and shadows remain subtle so transcript evidence and generated writing carry the visual weight.

## Information architecture

- Session rail: new chat and previous conversations
- Conversation: messages, citations, tool/skill status, and composer
- Artifact viewer: Markdown or isolated HTML/CSS preview
- Provider control: visible local/cloud selection and availability
- Source detail: episode metadata and the exact supporting excerpt

## Key states

- First-run guidance
- Empty conversation
- Retrieving evidence
- Generating locally or in the cloud
- Grounded answer with citations
- Insufficient evidence
- Artifact generated and previewed
- Provider unavailable
- Database unavailable

## Responsive behavior

Desktop uses a session rail, chat column, and optional artifact pane. Tablet collapses the session rail. Mobile presents chat and artifacts as switchable views, with citations in a bottom sheet.

## Accessibility

- Semantic headings and landmarks
- Keyboard-accessible session, citation, and artifact controls
- Visible focus indicators
- Status announcements through live regions
- Color contrast meeting WCAG AA
- No meaning communicated by color alone
- Reduced-motion support
