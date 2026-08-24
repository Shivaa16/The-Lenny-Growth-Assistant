import { ArrowUp, BookOpen, FileText, PanelRight, Plus, Sparkles } from "lucide-react";
import { FormEvent, useState } from "react";

const suggestions = [
  "How should an early-stage startup find product-market fit?",
  "What do the guests say about building a growth loop?",
  "Turn the answer into a Ship 30 for 30 essay"
];

export function App() {
  const [prompt, setPrompt] = useState("");
  const [submittedPrompt, setSubmittedPrompt] = useState<string | null>(null);

  function submit(event: FormEvent) {
    event.preventDefault();
    const value = prompt.trim();
    if (!value) return;
    setSubmittedPrompt(value);
    setPrompt("");
  }

  return (
    <main className="app-shell">
      <aside className="session-rail" aria-label="Conversation history">
        <div className="brand-mark" aria-label="Lenny Growth Assistant">L</div>
        <button className="rail-button active" aria-label="New conversation"><Plus size={19} /></button>
        <div className="rail-spacer" />
        <button className="avatar" aria-label="Evaluator profile">SK</button>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">LENNY GROWTH ASSISTANT</p>
            <h1>New conversation</h1>
          </div>
          <div className="topbar-actions">
            <span className="provider-pill"><span className="status-dot" /> Local · Qwen 2.5 3B</span>
            <button className="icon-button" aria-label="Open artifact viewer"><PanelRight size={19} /></button>
          </div>
        </header>

        <div className="conversation">
          {!submittedPrompt ? (
            <section className="welcome" aria-labelledby="welcome-title">
              <div className="sparkle"><Sparkles size={25} /></div>
              <p className="eyebrow">GROUNDED IN THE PODCAST</p>
              <h2 id="welcome-title">What are you trying to grow?</h2>
              <p className="welcome-copy">
                Ask a product or growth question. I’ll synthesize the most relevant lessons from
                Lenny’s Podcast and show exactly where they came from.
              </p>
              <div className="suggestions">
                {suggestions.map((suggestion, index) => (
                  <button key={suggestion} onClick={() => setPrompt(suggestion)}>
                    {index === 2 ? <FileText size={17} /> : <BookOpen size={17} />}
                    <span>{suggestion}</span>
                  </button>
                ))}
              </div>
            </section>
          ) : (
            <section className="message-preview" aria-live="polite">
              <div className="user-message">{submittedPrompt}</div>
              <div className="assistant-state">
                <Sparkles size={18} />
                <div>
                  <strong>Foundation connected.</strong>
                  <p>Transcript retrieval and grounded generation arrive in the next milestone.</p>
                </div>
              </div>
            </section>
          )}
        </div>

        <div className="composer-wrap">
          <form className="composer" onSubmit={submit}>
            <label className="sr-only" htmlFor="message">Ask about product or growth</label>
            <textarea
              id="message"
              rows={2}
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              placeholder="Ask about product, growth, or turn an answer into an artifact…"
            />
            <div className="composer-footer">
              <span>Answers include transcript sources</span>
              <button type="submit" aria-label="Send message" disabled={!prompt.trim()}><ArrowUp size={18} /></button>
            </div>
          </form>
          <p className="disclaimer">Grounded in indexed transcripts. Verify important decisions with the original episode.</p>
        </div>
      </section>
    </main>
  );
}

