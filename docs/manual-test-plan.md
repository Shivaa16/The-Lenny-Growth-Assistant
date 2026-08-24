# Manual UI Test Plan

Use the local Ollama configuration and a populated transcript index. Test desktop at 1440×900 and mobile at approximately 390×844.

## Primary demo flow

1. Open the app and confirm the header shows `Local` and the configured Ollama model.
2. Create a new conversation and send `Hi`; confirm it completes without transcript citations.
3. Ask: `How should an early-stage product build and measure a growth loop?`
4. Confirm the answer is readable, contains inline citation markers, and displays inspectable source cards.
5. Ask a contextual follow-up: `Which of those steps should happen first for a two-person team?`
6. Confirm the answer preserves context and provides transcript sources.
7. Choose **Ship 30 essay**; confirm the artifact pane opens beside chat and restores after reopening the session.
8. Choose **HTML brief**; confirm rendered content appears rather than raw HTML and no scripts or navigation execute.

## Failure and recovery states

1. Stop Ollama and ask a grounded question; expect an actionable provider/embedding error, not a blank screen.
2. Restart Ollama and retry successfully.
3. Ask a question outside the indexed collection; expect an explicit insufficient-evidence response.
4. Stop PostgreSQL; expect a storage-unavailable message with a retry action.
5. Enter only whitespace; confirm no request is sent.

## Persistence and isolation

1. Create two conversations with different topics.
2. Switch between them and confirm their messages and artifacts remain independent.
3. Refresh the browser and confirm conversation history is restored.
4. Inspect Network responses and confirm secrets and raw environment variables are absent.

## Responsive and accessibility checks

1. At mobile width, open and close the session drawer using its labeled buttons.
2. Open the artifact viewer; confirm it becomes a focused full-screen view and can be closed.
3. Navigate buttons, suggestions, composer, sources, session items, and artifact controls using only Tab/Shift+Tab and Enter.
4. Confirm every focused control has a visible outline and no content is clipped at 200% zoom.
5. Enable reduced motion and confirm loading remains understandable without relying on animation.

Record the date, browser, viewport, Ollama model, indexed transcript count, and any deviations when executing this plan.
