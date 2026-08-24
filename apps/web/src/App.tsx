import { AlertCircle, ArrowUp, BookOpen, FileText, Menu, PanelRight, Plus, Sparkles, X } from "lucide-react";
import { FormEvent, useCallback, useEffect, useState } from "react";

import {
  addMessage,
  ApiError,
  ConversationTurn,
  createSession,
  getProviderInfo,
  getSession,
  listSessions,
  Message,
  ProviderInfo,
  SessionSummary
} from "./api";

const suggestions = [
  "How should an early-stage startup find product-market fit?",
  "What do the guests say about building a growth loop?",
  "Turn the answer into a Ship 30 for 30 essay"
];

export function App() {
  const [prompt, setPrompt] = useState("");
  const [turn, setTurn] = useState<ConversationTurn | null>(null);
  const [history, setHistory] = useState<Message[]>([]);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [activeSession, setActiveSession] = useState<SessionSummary | null>(null);
  const [storageError, setStorageError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isResponding, setIsResponding] = useState(false);
  const [isMobileRailOpen, setIsMobileRailOpen] = useState(false);
  const [providerInfo, setProviderInfo] = useState<ProviderInfo | null>(null);

  const refreshSessions = useCallback(async () => {
    try {
      const result = await listSessions();
      setSessions(result.items);
      setStorageError(null);
    } catch (error) {
      setStorageError(error instanceof ApiError ? error.message : "Conversation storage is unavailable.");
    }
  }, []);

  useEffect(() => { void refreshSessions(); }, [refreshSessions]);
  useEffect(() => { void getProviderInfo().then(setProviderInfo).catch(() => undefined); }, []);

  async function startNewSession() {
    setIsCreating(true);
    try {
      const created = await createSession();
      setSessions((current) => [created, ...current]);
      setActiveSession(created);
      setTurn(null);
      setHistory([]);
      setStorageError(null);
    } catch (error) {
      setStorageError(error instanceof ApiError ? error.message : "Could not create a conversation.");
    } finally {
      setIsCreating(false);
    }
  }

  async function openSession(session: SessionSummary) {
    setActiveSession(session);
    setTurn(null);
    setIsMobileRailOpen(false);
    try {
      const detail = await getSession(session.id);
      setHistory(detail.messages);
      setStorageError(null);
    } catch (error) {
      setHistory([]);
      setStorageError(error instanceof ApiError ? error.message : "Could not load the conversation.");
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const value = prompt.trim();
    if (!value) return;
    let session = activeSession;
    if (!session) {
      try {
        session = await createSession();
        setSessions((current) => [session!, ...current]);
        setActiveSession(session);
      } catch (error) {
        setStorageError(error instanceof ApiError ? error.message : "Could not create a conversation.");
        return;
      }
    }
    try {
      setIsResponding(true);
      const completedTurn = await addMessage(session.id, value);
      setTurn(completedTurn);
      setHistory((current) => [
        ...current,
        completedTurn.user_message,
        completedTurn.assistant_message
      ]);
      setPrompt("");
      setStorageError(null);
      void refreshSessions();
    } catch (error) {
      setStorageError(error instanceof ApiError ? error.message : "Could not save the message.");
    } finally {
      setIsResponding(false);
    }
  }

  return (
    <main className="app-shell">
      {isMobileRailOpen && <button className="rail-overlay" aria-label="Close conversations" onClick={() => setIsMobileRailOpen(false)} />}
      <aside className={`session-rail${isMobileRailOpen ? " mobile-open" : ""}`} aria-label="Conversation history">
        <div className="brand-row"><div className="brand-mark" aria-hidden="true">L</div><div><strong>Lenny Growth</strong><span>Assistant</span></div><button className="rail-close" aria-label="Close conversations" onClick={() => setIsMobileRailOpen(false)}><X size={18} /></button></div>
        <button className="new-chat" onClick={startNewSession} disabled={isCreating}><Plus size={17} /><span>{isCreating ? "Creating…" : "New conversation"}</span></button>
        <p className="rail-label">RECENT</p>
        <nav className="session-list" aria-label="Recent conversations">
          {sessions.length ? sessions.map((session) => (
            <button key={session.id} className={session.id === activeSession?.id ? "active" : ""} onClick={() => void openSession(session)}>
              <span>{session.title}</span><small>{new Date(session.updated_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</small>
            </button>
          )) : <p className="no-sessions">Your saved conversations will appear here.</p>}
        </nav>
        <div className="rail-footer"><div className="avatar">SK</div><div><strong>Local evaluator</strong><span>Development workspace</span></div></div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <button className="mobile-menu" aria-label="Open conversations" onClick={() => setIsMobileRailOpen(true)}><Menu size={20} /></button>
          <div><p className="eyebrow">LENNY GROWTH ASSISTANT</p><h1>{activeSession?.title ?? "New conversation"}</h1></div>
          <div className="topbar-actions"><span className="provider-pill"><span className="status-dot" /> {providerInfo ? `${providerInfo.provider === "ollama" ? "Local" : "Cloud"} · ${providerInfo.model}` : "Provider loading"}</span><button className="icon-button" aria-label="Open artifact viewer"><PanelRight size={19} /></button></div>
        </header>

        {storageError && <div className="storage-alert" role="alert"><AlertCircle size={17} /><span>{storageError}</span><button onClick={() => void refreshSessions()}>Retry</button></div>}

        <div className="conversation">
          {history.length === 0 && !isResponding ? (
            <section className="welcome" aria-labelledby="welcome-title">
              <div className="sparkle"><Sparkles size={25} /></div><p className="eyebrow">GROUNDED IN THE PODCAST</p><h2 id="welcome-title">What are you trying to grow?</h2>
              <p className="welcome-copy">Ask a product or growth question. I’ll synthesize the most relevant lessons from Lenny’s Podcast and show exactly where they came from.</p>
              <div className="suggestions">{suggestions.map((suggestion, index) => <button key={suggestion} onClick={() => setPrompt(suggestion)}>{index === 2 ? <FileText size={17} /> : <BookOpen size={17} />}<span>{suggestion}</span></button>)}</div>
            </section>
          ) : (
            <section className="message-preview" aria-live="polite">
              {history.map((message) => message.role === "user" ? (
                <div className="user-message" key={message.id}>{message.content}</div>
              ) : message.role === "assistant" ? (
                <article className="assistant-answer" key={message.id}>
                  <div className="answer-icon"><Sparkles size={17} /></div>
                  <div>
                    <p>{message.content}</p>
                    {message.id === turn?.assistant_message.id && turn.citations.length > 0 && (
                      <section className="source-list" aria-label="Transcript sources">
                        <h3>Sources used</h3>
                        {turn.citations.map((citation) => (
                          <a key={citation.chunk_id} href={citation.youtube_url ?? undefined} target="_blank" rel="noreferrer">
                            <span className="source-number">{citation.position}</span>
                            <span>
                              <strong>{citation.title}</strong>
                              <small>{citation.guest} · Transcript passage {citation.position}</small>
                            </span>
                          </a>
                        ))}
                      </section>
                    )}
                  </div>
                </article>
              ) : null)}
              {isResponding && (
                <div className="assistant-state responding">
                  <Sparkles size={18} />
                  <div><strong>Searching the transcripts…</strong><p>Retrieving evidence and preparing a grounded answer.</p></div>
                </div>
              )}
            </section>
          )}
        </div>

        <div className="composer-wrap"><form className="composer" onSubmit={submit}><label className="sr-only" htmlFor="message">Ask about product or growth</label><textarea id="message" rows={2} value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="Ask about product, growth, or turn an answer into an artifact…" disabled={isResponding} /><div className="composer-footer"><span>Answers include transcript sources</span><button type="submit" aria-label="Send message" disabled={!prompt.trim() || isResponding}><ArrowUp size={18} /></button></div></form><p className="disclaimer">Grounded in indexed transcripts. Verify important decisions with the original episode.</p></div>
      </section>
    </main>
  );
}
