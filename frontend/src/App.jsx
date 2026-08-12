import { useEffect, useMemo, useState } from "react";
import "./App.css";

const formatLabel = (value = "") =>
  value.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());

function StatusPill({ children, tone = "good" }) {
  return <span className={`status-pill ${tone}`}>{children}</span>;
}

function NodeCard({ node, index, onSelect, selected = false }) {
  return (
    <div className={`graph-row ${selected ? "node-selected" : ""}`}>
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
          <span>{node.responsible_role}</span>
        </div>

        <StatusPill
          tone={
            node.status === "COMPLETED"
              ? "good"
              : node.status === "BLOCKED" || node.status === "STALE"
                ? "bad"
                : "neutral"
          }
        >
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

  useEffect(() => {
    fetch("/studio-snapshot.json")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Unable to load production snapshot.");
        }
        return response.json();
      })
      .then(setSnapshot)
      .catch((err) => setError(err.message));
  }, []);

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
    <main className="app-shell">
      <div className="ambient-grid" />

      <header className="topbar">
        <div>
          <p className="eyebrow">Kevaro Studio Command</p>
          <h1>Studio Command Center</h1>
        </div>

        <div className="topbar-status">
          <span className="live-dot" />
          Governed Production Runtime
        </div>
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
              <h3>Autonomous production orchestration</h3>
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
