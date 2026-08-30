import { useEffect, useMemo, useState } from "react";
import "./App.css";

const formatLabel = (value = "") =>
  String(value).replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());

const compactValue = (value) => {
  if (value == null || value === "") return null;
  if (typeof value === "string" || typeof value === "number") return String(value);
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value)) {
    const simple = value.filter((item) => ["string", "number"].includes(typeof item));
    return simple.length ? simple.slice(0, 4).join(" • ") : null;
  }
  return null;
};

const statusTone = (status = "") => {
  const value = String(status).toUpperCase();
  if (["COMPLETED", "APPROVED", "VERIFIED", "READY_FOR_DELIVERY"].includes(value)) return "good";
  if (["BLOCKED", "STALE", "REJECTED", "UNAVAILABLE"].includes(value)) return "bad";
  return "neutral";
};

function StatusPill({ children, tone = "good" }) {
  return <span className={`status-pill ${tone}`}>{children}</span>;
}

function NodeCard({ node, index, onSelect, selected = false, active = false }) {
  const access = node.ownership?.access;
  return (
    <div className={"graph-row " + (selected ? "node-selected " : "") + (active ? "node-current" : "")} style={{ "--wake-delay": index * 90 + "ms" }}>
      <div className="graph-index">{String(index + 1).padStart(2, "0")}</div>

      <div className="graph-line">
        <span className="node-dot" />
        <span className="connector" />
      </div>

      <button
        type="button"
        className="graph-card graph-card-button"
        onClick={() => onSelect(node.node_id)}
      >
        <div>
          <strong>{node.task_name}</strong>
          <span>{node.accountability?.human_owner?.name ? node.accountability.human_owner.name + " · " : ""}{node.accountability?.ai_agent_responsible?.name || node.responsible_role}</span>
          {access?.access_level && <small>{formatLabel(access.access_level)} access</small>}
        </div>

        <StatusPill tone={statusTone(node.status)}>
          {formatLabel(node.status)}
        </StatusPill>
      </button>
    </div>
  );
}

function App() {
  const [snapshot, setSnapshot] = useState(null);
  const [error, setError] = useState("");
  const [realityReason, setRealityReason] = useState(
    "Launch moved from Friday to Wednesday."
  );
  const [realityOrigin, setRealityOrigin] = useState("Scheduling");
  const [realityResult, setRealityResult] = useState(null);
  const [realityBusy, setRealityBusy] = useState(false);
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [introVisible, setIntroVisible] = useState(true);
  const [runtimeStatus, setRuntimeStatus] = useState(null);
  const [assetNotice, setAssetNotice] = useState("");
  const [assetBusy, setAssetBusy] = useState(false);
  const [productionName, setProductionName] = useState("");
  const [currentCrew, setCurrentCrew] = useState(null);
  const [authConfig, setAuthConfig] = useState(null);
  const [localSubject, setLocalSubject] = useState("");
  const [signInRequired, setSignInRequired] = useState(false);
  const [snapshotMode, setSnapshotMode] = useState("CONNECTING");
  const [snapshotEndpoint, setSnapshotEndpoint] = useState("");

  useEffect(() => {
    let cancelled = false;

    const loadSnapshot = async () => {
      try {
        let bootstrapResponse = await fetch("/api/studio-snapshot");
        if (!bootstrapResponse.ok) bootstrapResponse = await fetch("/studio-snapshot.json");
        if (!bootstrapResponse.ok) throw new Error("Unable to resolve the current production identity.");
        const bootstrap = await bootstrapResponse.json();
        if (!bootstrap.production_name) throw new Error("Production identity is missing from the runtime snapshot.");
        if (!cancelled) setProductionName(bootstrap.production_name);
        const sessionResponse = await fetch("/api/auth/session?production_name=" + encodeURIComponent(bootstrap.production_name));
        if (sessionResponse.status === 401) { if (!cancelled) setSignInRequired(true); return; }
        if (!sessionResponse.ok) throw new Error("Your crew account is not assigned to this production.");
        const session = await sessionResponse.json();
        if (!cancelled) setCurrentCrew(session.crew);

        const endpoint = "/api/productions/" + encodeURIComponent(bootstrap.production_name) + "/studio-snapshot";
        const liveResponse = await fetch(endpoint);
        if (!liveResponse.ok) throw new Error("Live production state is unavailable.");
        const liveSnapshot = await liveResponse.json();
        if (liveSnapshot.production_name !== bootstrap.production_name) throw new Error("Live production identity does not match the runtime context.");
        if (!cancelled) { setSnapshot(liveSnapshot); setSnapshotMode("LIVE"); setSnapshotEndpoint(endpoint); }
      } catch (liveError) {
        try {
          const fallbackResponse = await fetch("/studio-snapshot.json");
          if (!fallbackResponse.ok) throw liveError;
          const fallbackSnapshot = await fallbackResponse.json();
          if (!cancelled) { setSnapshot(fallbackSnapshot); setSnapshotMode("FALLBACK"); setSnapshotEndpoint("/studio-snapshot.json"); }
        } catch (fallbackError) {
          if (!cancelled) setError(fallbackError.message || liveError.message);
        }
      }
    };

    loadSnapshot();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    fetch("/api/auth/config").then((response) => response.ok ? response.json() : null).then(setAuthConfig).catch(() => setAuthConfig(null));
  }, []);

  useEffect(() => {
    if (authConfig?.provider !== "google" || !authConfig.google_client_id || !signInRequired) return;
    const start = () => window.google?.accounts.id.initialize({
      client_id: authConfig.google_client_id,
      callback: async ({ credential }) => {
        const response = await fetch("/api/auth/google", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ credential }) });
        if (response.ok) window.location.reload(); else setError("Google account is not assigned to this production.");
      },
    });
    if (window.google?.accounts) { start(); window.google.accounts.id.renderButton(document.getElementById("google-sign-in"), { theme: "filled_black", size: "large" }); return; }
    const script = document.createElement("script"); script.src = "https://accounts.google.com/gsi/client"; script.async = true; script.onload = () => { start(); window.google.accounts.id.renderButton(document.getElementById("google-sign-in"), { theme: "filled_black", size: "large" }); }; document.head.appendChild(script);
  }, [authConfig, signInRequired]);

  useEffect(() => {
    const timer = window.setTimeout(() => setIntroVisible(false), 2500);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    fetch("/health")
      .then((response) => response.ok ? response.json() : null)
      .then((payload) => setRuntimeStatus(payload?.runtime_configuration || null))
      .catch(() => setRuntimeStatus(null));
  }, []);

  const localSignIn = async () => {
    const response = await fetch("/api/auth/local", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ auth_subject: localSubject.trim() }) });
    if (response.ok) window.location.reload(); else setError("Local crew identity is not provisioned.");
  };

  const signOut = async () => { await fetch("/api/auth/sign-out", { method: "POST" }); window.location.reload(); };

  const registerBrowserAsset = async (file) => {
    if (!file || !snapshot) return;
    setAssetBusy(true); setAssetNotice("Registering governed asset…");
    try {
      const content = await new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(String(reader.result).split(",")[1]); reader.onerror = reject; reader.readAsDataURL(file); });
      const node = snapshot.graph.nodes.find((item) => item.node_id === "Asset & Media") || snapshot.graph.nodes[0];
      const response = await fetch("/api/productions/" + encodeURIComponent(snapshot.production_name) + "/assets/register", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ node_id: node.node_id, asset_category: file.type.startsWith("video/") ? "VIDEO" : file.type.startsWith("audio/") ? "AUDIO" : file.type.startsWith("image/") ? "IMAGE" : "OTHER_PRODUCTION_FILE", filename: file.name, display_name: file.name, media_document_type: file.type || "application/octet-stream", content_base64: content, content_type: file.type || "application/octet-stream", provenance: { source: "authenticated browser upload" } }) });
      if (!response.ok) throw new Error((await response.json()).detail?.reason || "Asset registration was not authorized.");
      const refreshed = await fetch(snapshotEndpoint); setSnapshot(await refreshed.json()); setAssetNotice("Asset registered and production snapshot refreshed.");
    } catch (uploadError) { setAssetNotice(uploadError.message); } finally { setAssetBusy(false); }
  };

  const metrics = useMemo(() => {
    if (!snapshot) return null;

    const graph = snapshot.graph;
    const total = graph.nodes.length;
    const completed = graph.completed_nodes.length;

    return {
      total,
      completed,
      progress: total ? Math.round((completed / total) * 100) : 0,
      blockers: graph.blocked_nodes.length,
      stale: graph.stale_nodes.length,
    };
  }, [snapshot]);

  if (signInRequired) {
    return (
      <main className="loading-screen sign-in-screen">
        <p className="eyebrow">Kevaro Studio Command · Authenticated Crew</p>
        <h1>Sign in to enter the production.</h1>
        <p>{productionName || "Governed production"} resolves your role, ownership, and review authority server-side.</p>
        <div id="google-sign-in" />
        {authConfig?.local_auth_enabled && <div className="local-sign-in"><input value={localSubject} onChange={(event) => setLocalSubject(event.target.value)} placeholder="Provisioned local auth subject" /><button type="button" onClick={localSignIn} disabled={!localSubject.trim()}>LOCAL TEST SIGN IN</button></div>}
        <small>Roles and Studio Head authority cannot be supplied by this browser.</small>
      </main>
    );
  }

  if (error) {
    return (
      <main className="loading-screen">
        <p className="eyebrow">Kevaro Studio Command</p>
        <h1>Production data unavailable</h1>
        <p>{error}</p>
      </main>
    );
  }

  if (!snapshot || !metrics) {
    return (
      <main className="loading-screen">
        <div className="loader" />
        <p>Loading governed production state...</p>
      </main>
    );
  }

  const delivery = snapshot.delivery;
  const evidence = snapshot.evidence_summary || {};
  const guidance = snapshot.guidance || {};
  const assetWorkflow = snapshot.production_assets || { assets: [], asset_count: 0, approved_asset_count: 0, missing_deliverables: [] };
  const activeNodeId = snapshot.graph.running_nodes?.[0] || snapshot.graph.ready_nodes?.[0] || (snapshot.graph.graph_complete ? "Final Package" : null);
  const selectedArtifact = selectedNodeId ? (snapshot.node_intelligence?.[selectedNodeId] || snapshot.graph.nodes.find((node) => node.node_id === selectedNodeId)?.artifact) : null;

  const displayNodes = snapshot.graph.nodes.map((node) => {
    if (!realityResult) return node;

    if (realityResult.stale_nodes?.includes(node.node_id)) {
      return {
        ...node,
        status: "STALE",
        stale_reason: realityResult.reason,
      };
    }

    return node;
  });

  const nodes = displayNodes;

  const selectedNode =
    nodes.find((node) => node.node_id === selectedNodeId) || null;

  const selectedNodeImpact = selectedNode
    ? {
        preserved:
          realityResult?.preserved_nodes?.includes(selectedNode.node_id) ?? false,
        stale:
          realityResult?.stale_nodes?.includes(selectedNode.node_id) ?? false,
        changed:
          realityResult?.changed_nodes?.includes(selectedNode.node_id) ?? false,
      }
    : null;

  const submitRealityShift = async () => {
    if (!realityReason.trim()) return;

    setRealityBusy(true);
    setError("");

    try {
      const response = await fetch("/api/reality-shift", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          changed_node_ids: [realityOrigin],
          reason: realityReason.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error("Kevaro could not evaluate the production reality shift.");
      }

      const result = await response.json();
      setRealityResult(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setRealityBusy(false);
    }
  };

  const resetRealityShift = () => {
    setRealityResult(null);
  };

  const scheduling = nodes.find((node) => node.node_id === "Scheduling");
  const assetMedia = nodes.find((node) => node.node_id === "Asset & Media");

  const parallelNames = new Set(["Scheduling", "Asset & Media"]);

  const sequentialNodes = nodes.filter(
    (node) => !parallelNames.has(node.node_id),
  );

  const planningIndex = sequentialNodes.findIndex(
    (node) => node.node_id === "Production Planning",
  );

  const beforeParallel = sequentialNodes.slice(0, planningIndex + 1);
  const afterParallel = sequentialNodes.slice(planningIndex + 1);

  return (
    <main className={"app-shell " + (introVisible ? "intro-active" : "")}>
      <section className={"cinematic-intro " + (introVisible ? "intro-visible" : "intro-dismissed")} aria-hidden={!introVisible}>
        <div className="intro-frame">
          <p>KEVARO</p><h2>Studio Command</h2>
          <div className="intro-rule" />
          <span>ORCHESTRATION ONLINE · EVIDENCE CONNECTED · HUMAN AUTHORITY SECURED</span>
        </div>
        <button type="button" onClick={() => setIntroVisible(false)}>ENTER COMMAND CENTER</button>
      </section>
      <div className="ambient-grid" />

      <header className="topbar">
        <div>
          <p className="eyebrow">Kevaro Studio Command</p>
          <h1>Studio Command Center</h1>
        </div>

        <div className="topbar-status">
          <span className="live-dot" />
          Governed Production Runtime
          <strong className={"snapshot-mode " + snapshotMode.toLowerCase()} title={snapshotEndpoint}>{snapshotMode === "LIVE" ? "LIVE PRODUCTION" : snapshotMode === "FALLBACK" ? "STATIC FALLBACK" : "CONNECTING"}</strong>
        </div>
        <div className="crew-session"><span>{currentCrew?.display_name || "Crew"}</span><strong>{currentCrew?.studio_head ? "Studio Head" : currentCrew?.roles?.join(" · ") || "Assigned crew"}</strong><button type="button" onClick={signOut}>Sign out</button></div><button className="replay-intro" type="button" onClick={() => setIntroVisible(true)}>Replay opening</button>
      </header>

      <section className="architecture-strip">
        <span>Gemini</span>
        <i />
        <span>Google ADK</span>
        <i />
        <span>Governed Agent Graph</span>
        <i />
        <span>Parallel Production</span>
        <i />
        <span>Human Final Authority</span>

        <div className="operating-signature">
          <span>EVIDENCE</span>
          <b>→</b>
          <span>DECISION</span>
          <b>→</b>
          <span>EXECUTION</span>
        </div>
      </section>

      <section className="decision-spine" aria-label="Governed production sequence">
        {["Evidence", "Agent Work", "Verification", "Human Decision", "Delivery"].map((step, index) => (
          <div key={step}><span>{String(index + 1).padStart(2, "0")}</span><strong>{step}</strong></div>
        ))}
      </section>

      <section className="command-guidance">
        <div><p className="eyebrow">Role-Aware Command</p><h2>Your work, without the training burden.</h2><span>{formatLabel(snapshot.guidance_level || "Standard")} guidance · Studio Head view</span></div>
        <article><small>YOUR WORK NOW</small><strong>{guidance.your_work_now?.[0] || "Monitor governed production state"}</strong></article>
        <article><small>WAITING ON</small><strong>{guidance.waiting_on?.[0] || "No active dependency"}</strong></article>
        <article><small>NEEDS ATTENTION</small><strong>{guidance.needs_attention?.join(" · ") || "No unresolved attention items"}</strong></article>
        <article className="next-action"><small>NEXT BEST ACTION</small><strong>{guidance.next_best_action?.instruction || guidance.next_best_action?.action_type || "Review the final governed package"}</strong></article>
      </section>

      <section className={`reality-console ${realityResult ? "shift-active" : ""}`}>
        <div className="reality-console-copy">
          <p className="eyebrow">Production Reality Engine</p>
          <h2>
            {realityResult
              ? "Reality shifted. Kevaro recalculated the production."
              : "What changed in the real world?"}
          </h2>

          <p>
            Kevaro does not blindly restart the plan. It protects work that is
            still true, invalidates only what the change affects, and restores
            human authority before consequential execution continues.
          </p>
        </div>

        <div className="reality-controls">
          <label>
            <span>Impact Origin</span>
            <select
              value={realityOrigin}
              onChange={(event) => setRealityOrigin(event.target.value)}
              disabled={realityBusy}
            >
              <option value="Production Brief">Production Brief</option>
              <option value="Research">Research</option>
              <option value="Creative Development">Creative Development</option>
              <option value="Production Planning">Production Planning</option>
              <option value="Scheduling">Scheduling</option>
              <option value="Asset & Media">Asset & Media</option>
              <option value="Clearance & Compliance">Clearance & Compliance</option>
            </select>
          </label>

          <label className="reality-input">
            <span>Reality Shift</span>
            <textarea
              value={realityReason}
              onChange={(event) => setRealityReason(event.target.value)}
              placeholder="Example: Launch moved from Friday to Wednesday and celebrity talent was removed."
              rows="3"
              disabled={realityBusy}
            />
          </label>

          <div className="reality-actions">
            <button
              className="reality-primary"
              type="button"
              onClick={submitRealityShift}
              disabled={realityBusy || !realityReason.trim()}
            >
              {realityBusy ? "RECALCULATING…" : "DECLARE REALITY SHIFT"}
            </button>

            {realityResult && (
              <button
                className="reality-secondary"
                type="button"
                onClick={resetRealityShift}
              >
                RESTORE KNOWN-GOOD VIEW
              </button>
            )}
          </div>
        </div>

        {realityResult && (
          <div className="impact-intelligence">
            <div className="impact-banner">
              <span className="impact-pulse" />
              <div>
                <small>REALITY SHIFT DETECTED</small>
                <strong>{realityResult.reason}</strong>
              </div>
            </div>

            <div className="impact-grid">
              <article>
                <span>PRESERVED</span>
                <strong>{realityResult.preserved_nodes.length}</strong>
                <p>known-good work protected</p>
              </article>

              <article className="impact-stale">
                <span>STALE</span>
                <strong>{realityResult.stale_nodes.length}</strong>
                <p>work requiring recalculation</p>
              </article>

              <article className="impact-human">
                <span>HUMAN AUTHORITY</span>
                <strong>
                  {realityResult.human_decision_required ? "REQUIRED" : "CLEAR"}
                </strong>
                <p>consequential execution gate</p>
              </article>
            </div>

            <div className="impact-lists">
              <div>
                <span>Still safe to trust</span>
                <p>{realityResult.preserved_nodes.join(" • ")}</p>
              </div>

              <div>
                <span>Must be reconsidered</span>
                <p>{realityResult.stale_nodes.join(" • ")}</p>
              </div>
            </div>
          </div>
        )}
      </section>

      <section className="hero-panel">
        <div className="hero-copy">
          <div className="hero-meta">
            <StatusPill>{formatLabel(snapshot.approval_status)}</StatusPill>
            <span>Decision #{snapshot.decision_sequence}</span>
            <span className="system-state">System State Verified</span>
          </div>

          <h2>{snapshot.production_name}</h2>

          <p>
            One Studio Head directive became a governed production operation.
            Kevaro coordinated evidence, creative development, production
            planning, parallel execution, clearance, independent QA, human
            authority, and final delivery.
          </p>

          <div className="stage-line">
            <span>Current Stage</span>
            <strong>{formatLabel(snapshot.current_stage)}</strong>
          </div>
        </div>

        <div className="readiness-card">
          <div className="readiness-orbit">
            <div className="readiness-orbit-inner">
              <span>{delivery?.readiness_score ?? metrics.progress}%</span>
              <small>READY</small>
            </div>
          </div>

          <span className="metric-label">Production Readiness</span>

          <div className="progress-track">
            <div
              className="progress-fill"
              style={{
                width: `${delivery?.readiness_score ?? metrics.progress}%`,
              }}
            />
          </div>

          <small>
            {snapshot.execution_authorized
              ? "Execution authorized by governed state"
              : "Execution blocked"}
          </small>
        </div>
      </section>

      <section className="metric-grid">
        <article className="metric-card">
          <span className="metric-label">Workflow</span>
          <strong>
            {metrics.completed}/{metrics.total}
          </strong>
          <p>production nodes completed</p>
        </article>

        <article className="metric-card">
          <span className="metric-label">Blocked</span>
          <strong>{metrics.blockers}</strong>
          <p>active production blockers</p>
        </article>

        <article className="metric-card">
          <span className="metric-label">Stale Work</span>
          <strong>{metrics.stale}</strong>
          <p>artifacts requiring refresh</p>
        </article>

        <article className="metric-card authority-metric">
          <span className="metric-label">Human Authority</span>
          <strong>1</strong>
          <p>final Studio Head decision gate</p>
        </article>
      </section>

      <section className="content-grid">
        <article className="panel graph-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Live Production Graph</p>
              <h3>Governed production orchestration</h3>
            </div>

            <StatusPill>
              {snapshot.graph.graph_complete ? "Graph Complete" : "In Progress"}
            </StatusPill>
          </div>

          <div className="graph">
            <div className="graph-heartbeat" aria-hidden="true">
              <span />
            </div>
            {beforeParallel.map((node, index) => (
              <NodeCard
                node={node}
                index={index}
                key={node.node_id}
                onSelect={setSelectedNodeId}
                selected={selectedNodeId === node.node_id}
                active={activeNodeId === node.node_id}
              />
            ))}

            {scheduling && assetMedia && (
              <div className="parallel-block">
                <div className="branch-origin">
                  <span />
                  <strong>SPLIT</strong>
                  <span />
                </div>
                <div className="parallel-header">
                  <span>Parallel Production Execution</span>
                  <small>Two workstreams • one governed state</small>
                </div>

                <div className="parallel-split">
                  <span />
                  <span />
                </div>

                <div className="parallel-lanes">
                  {[scheduling, assetMedia].map((node, index) => (
                    <div className="parallel-card" key={node.node_id}>
                      <div className="parallel-lane-label">
                        Lane {index === 0 ? "A" : "B"}
                      </div>

                      <strong>{node.task_name}</strong>
                      <span>{node.responsible_role}</span>

                      <StatusPill tone="good">
                        {formatLabel(node.status)}
                      </StatusPill>
                    </div>
                  ))}
                </div>

                <div className="reconverge">
                  <span />
                  <strong>RECONVERGE</strong>
                  <span />
                </div>

                <div className="merge-pulse">
                  <span />
                </div>
              </div>
            )}

            {afterParallel.map((node, index) => (
              <NodeCard
                node={node}
                index={beforeParallel.length + 2 + index}
                key={node.node_id}
                onSelect={setSelectedNodeId}
                selected={selectedNodeId === node.node_id}
                active={activeNodeId === node.node_id}
              />
            ))}
          </div>
        </article>

        {selectedNode && (
          <section className="node-intelligence-panel">
            <div className="node-intelligence-header">
              <div>
                <p className="eyebrow">NODE INTELLIGENCE</p>
                <h2>{selectedNode.task_name}</h2>
                <span>{selectedNode.responsible_role}</span>
              </div>

              <button
                type="button"
                className="node-intelligence-close"
                onClick={() => setSelectedNodeId(null)}
                aria-label="Close node intelligence"
              >
                ×
              </button>
            </div>

            <div className="node-intelligence-grid">
              <div>
                <span className="eyebrow">CURRENT STATE</span>
                <strong>{formatLabel(selectedNode.status)}</strong>
              </div>

              <div>
                <span className="eyebrow">REALITY IMPACT</span>
                <strong>
                  {!realityResult
                    ? "KNOWN-GOOD"
                    : selectedNodeImpact?.changed
                      ? "ORIGIN"
                      : selectedNodeImpact?.stale
                        ? "REASSESSMENT REQUIRED"
                        : selectedNodeImpact?.preserved
                          ? "PRESERVED"
                          : "UNCHANGED"}
                </strong>
              </div>
            </div>

            <div className="node-intelligence-explanation">
              {!realityResult ? (
                <p>
                  This node belongs to the current known-good production state.
                  Declare a Reality Shift to see how Kevaro evaluates its impact.
                </p>
              ) : selectedNodeImpact?.changed ? (
                <p>
                  This is the origin of the declared real-world change. Kevaro
                  propagated impact from this point through the production graph.
                </p>
              ) : selectedNodeImpact?.stale ? (
                <p>
                  This work can no longer be trusted without recalculation because
                  it depends directly or indirectly on information changed by the
                  Reality Shift.
                </p>
              ) : selectedNodeImpact?.preserved ? (
                <p>
                  Kevaro preserved this work because its evidence remains valid
                  after the Reality Shift. It does not need to be repeated.
                </p>
              ) : (
                <p>
                  This node was not materially affected by the declared Reality
                  Shift.
                </p>
              )}
            </div>

            <div className="dossier-grid">
              <article><small>OWNER / AGENT</small><strong>{selectedNode.accountability?.human_owner?.name || "Human owner not assigned"} · {selectedNode.accountability?.ai_agent_responsible?.name || selectedNode.responsible_role}</strong></article>
              <article><small>ACCESS / OWNERSHIP</small><strong>{formatLabel(selectedNode.ownership?.access?.access_level || snapshot.access?.[selectedNode.node_id]?.access_level || "Read governed state")}</strong></article>
              <article><small>NEXT BEST ACTION</small><strong>{selectedNode.guidance?.next_best_action?.instruction || selectedNode.guidance?.next_best_action?.action_type || "Review node artifact and dependencies"}</strong></article>
              <article><small>WAITING ON / BLOCKERS</small><strong>{selectedNode.guidance?.blockers?.join(" · ") || selectedNode.guidance?.waiting_on?.join(" · ") || selectedNode.dependencies?.join(" · ") || "No active blockers"}</strong></article>
            </div>
            {selectedArtifact && typeof selectedArtifact === "object" && (
              <div className="artifact-dossier"><span className="eyebrow">GOVERNED ARTIFACT</span>
                <div>{Object.entries(selectedArtifact).filter(([, value]) => compactValue(value)).slice(0, 8).map(([key, value]) => (
                  <article key={key}><small>{formatLabel(key)}</small><p>{compactValue(value)}</p></article>
                ))}</div>
              </div>
            )}

            {selectedNode.stale_reason && (
              <div className="node-intelligence-reason">
                <span className="eyebrow">WHY IT CHANGED</span>
                <p>{selectedNode.stale_reason}</p>
              </div>
            )}
          </section>
        )}

        <aside className="side-column">
          <article className="panel decision-panel">
            <div className="human-gate">
              <div className="authority-lock" aria-hidden="true">
                <span className="authority-lock-shackle" />
                <span className="authority-lock-body" />
              </div>
              <span>HUMAN AUTHORITY GATE</span>
            </div>

            <p className="eyebrow">Studio Head Authority</p>
            <h3>{formatLabel(snapshot.approval_status)}</h3>

            <p>
              Kevaro may coordinate, verify, protect, and recommend. Final
              consequential authority remains human.
            </p>

            <div className="authority-rule">
              KEVARO ADVISES
              <span>→</span>
              STUDIO HEAD DECIDES
            </div>

            <div className="decision-detail">
              <span>Decision Sequence</span>
              <strong>#{snapshot.decision_sequence}</strong>
            </div>

            <div className="decision-detail">
              <span>Execution</span>
              <strong>
                {snapshot.execution_authorized ? "Authorized" : "Blocked"}
              </strong>
            </div>

            <div className="decision-detail">
              <span>Corrective Cycle</span>
              <strong>
                {snapshot.corrective_cycle_active ? "Active" : "Clear"}
              </strong>
            </div>
          </article>

          <article className="panel memory-panel">
            <p className="eyebrow">Production Memory</p>
            <h3>Known-good state protected</h3>

            <div className="memory-stat">
              <strong>{snapshot.preserved_artifacts.length}</strong>
              <span>preserved artifacts</span>
            </div>

            <div className="memory-stat">
              <strong>{snapshot.stale_artifacts.length}</strong>
              <span>stale artifacts</span>
            </div>

            <div className="memory-state">
              <span className="memory-pulse" />
              Recovery State Available
            </div>
          </article>
        </aside>
      </section>

      <section className="evidence-room">
        <div className="evidence-heading"><div><p className="eyebrow">Parallel Evidence Room</p><h2>Evidence that can be inspected, not merely trusted.</h2></div><StatusPill tone={statusTone(evidence.status)}>{evidence.provider || "Parallel"} · {formatLabel(evidence.status || "Not Recorded")}</StatusPill></div>
        <div className="evidence-stats"><article><small>RESEARCH QUERY</small><strong>{evidence.query?.objective || evidence.query?.search_queries?.[0] || "No query recorded in this snapshot"}</strong></article><article><small>GROUNDED SOURCES</small><strong>{evidence.grounded_source_count ?? 0}</strong></article><article><small>LAST EVIDENCE REFRESH</small><strong>{evidence.last_invocation_at ? new Date(evidence.last_invocation_at).toLocaleString() : "Not recorded"}</strong></article><article><small>EVIDENCE GAPS</small><strong>{evidence.evidence_gaps?.length || 0}</strong></article></div>
        <div className="citation-list">{evidence.most_relevant_citations?.length ? evidence.most_relevant_citations.map((citation, index) => (<a href={citation.url} target="_blank" rel="noreferrer" key={citation.url}><span>{citation.citation_id || String(index + 1).padStart(2, "0")}</span><div><strong>{citation.title || citation.source || "Grounded source"}</strong><small>{citation.relevance || citation.finding || "Parallel-sourced evidence"}</small></div><b>↗</b></a>)) : <p className="empty-proof">No citations are present in this snapshot. Kevaro does not fabricate evidence.</p>}</div>
        {!!evidence.evidence_gaps?.length && <div className="evidence-gaps"><small>OPEN EVIDENCE GAPS</small><p>{evidence.evidence_gaps.join(" · ")}</p></div>}
      </section>

      <section className="asset-ingress">
        <div className="asset-heading"><div><p className="eyebrow">Production Asset Ingress</p><h2>Create in the right tool. Govern it here.</h2></div><div><strong>{assetWorkflow.approved_asset_count || 0}/{assetWorkflow.asset_count || 0}</strong><span>assets approved</span></div></div>
        <div className="asset-list">{assetWorkflow.assets?.length ? assetWorkflow.assets.map((asset) => (<article key={asset.asset_id}><div><small>{formatLabel(asset.asset_category || "Production asset")}</small><strong>{asset.display_name || asset.filename || asset.asset_id}</strong><span>Version {asset.latest_version?.version_number || asset.version_number || 1} · {formatLabel(asset.review_state || asset.status)}</span></div><StatusPill tone={statusTone(asset.review_state || asset.status)}>{formatLabel(asset.handoff_state || asset.review_state || asset.status)}</StatusPill></article>)) : <p className="empty-proof">No governed assets are registered in this snapshot. Upload creates a new version; it never silently replaces prior work.</p>}</div>
        <div className="asset-actions"><label className="ingress-button">{assetBusy ? "REGISTERING…" : "REGISTER ASSET"}<input type="file" hidden disabled={assetBusy || !currentCrew} onChange={(event) => registerBrowserAsset(event.target.files?.[0])} /></label><button type="button" disabled>EXTERNAL TOOL HANDOFF</button><span>{assetNotice || (currentCrew ? `Signed in as  · server-scoped authority` : "Sign in to register assets")}</span></div>
      </section>

      {runtimeStatus && <section className="runtime-proof"><span>Runtime proof</span>{Object.entries(runtimeStatus).map(([key, value]) => <div key={key}><i className={value === "configured" || value === "enabled" ? "ok" : ""} />{formatLabel(key)} <strong>{formatLabel(value)}</strong></div>)}</section>}

      {delivery && (
        <section className="delivery-panel">
          <div className="delivery-beam" />
          <div className="delivery-glow" />

          <div className="delivery-sweep" aria-hidden="true" />

          <div className="delivery-copy">
            <p className="eyebrow">Final Production Package</p>
            <h2>READY FOR DELIVERY</h2>

            <p>
              Approved creative, production evidence, governance history,
              clearance, independent QA, and final assets have converged into
              one governed delivery package.
            </p>

            <div className="delivery-signature">
              Governed • Verified • Human Approved
            </div>
          </div>

          <div className="delivery-assets">
            {delivery.delivery_artifacts.map((artifact) => (
              <div className="delivery-item" key={artifact}>
                <span>✓</span>
                {artifact}
              </div>
            ))}
          </div>

          <div className="ready-mark">
            <div className="completion-ring">
              <div>
                <span>{delivery.readiness_score}%</span>
                <strong>READY</strong>
              </div>
            </div>
          </div>
        </section>
      )}

      <footer>
        <span>Kevaro Studio Command</span>
        <span>
          One Studio Head. One directive. An autonomous production operation.
        </span>
      </footer>
    </main>
  );
}

export default App;
