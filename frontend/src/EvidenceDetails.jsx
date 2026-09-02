const safeExternalUrl = (value) => {
  if (typeof value !== "string" || !value.trim()) return null;
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) ? url.href : null;
  } catch {
    return null;
  }
};

export default function EvidenceDetails({
  evidence,
  compact = false,
  formatLabel,
  statusTone,
  StatusPill,
}) {
  const citations = Array.isArray(evidence?.most_relevant_citations)
    ? evidence.most_relevant_citations : [];
  const findings = Array.isArray(evidence?.findings) ? evidence.findings : [];
  const gaps = Array.isArray(evidence?.evidence_gaps) ? evidence.evidence_gaps : [];

  return (
    <div className={compact ? "evidence-details evidence-details-compact" : "evidence-details"}>
      <div className="evidence-heading">
        <div>
          <p className="eyebrow">{compact ? "LIVE GOVERNED EVIDENCE" : "Parallel Evidence Room"}</p>
          <h2>{compact ? "Research evidence" : "Evidence that can be inspected, not merely trusted."}</h2>
        </div>
        <StatusPill tone={statusTone(evidence?.status)}>
          {evidence?.provider || "Parallel"} · {formatLabel(evidence?.status || "Not Recorded")}
        </StatusPill>
      </div>
      <div className="evidence-stats">
        <article><small>RESEARCH QUERY</small><strong>{evidence?.query?.objective || evidence?.query?.search_queries?.[0] || "No query recorded in the governed state"}</strong></article>
        <article><small>GROUNDED SOURCES</small><strong>{evidence?.grounded_source_count ?? 0}</strong></article>
        <article><small>LAST EVIDENCE REFRESH</small><strong>{evidence?.last_invocation_at ? new Date(evidence.last_invocation_at).toLocaleString() : "Not recorded"}</strong></article>
        <article><small>EVIDENCE GAPS</small><strong>{gaps.length}</strong></article>
      </div>
      {!!findings.length && <div className="evidence-findings">
        {findings.map((item, index) => <article key={item.research_question || index}>
          <small>{item.research_question || "Research finding"}</small>
          <strong>{item.finding || "No finding recorded"}</strong>
          {item.production_impact && <p>{item.production_impact}</p>}
        </article>)}
      </div>}
      <div className="citation-list">
        {citations.length ? citations.map((citation, index) => {
          const href = safeExternalUrl(citation.url);
          const content = <>
            <span>{citation.citation_id || String(index + 1).padStart(2, "0")}</span>
            <div>
              <strong>{citation.title || citation.source || "Recorded source"}</strong>
              <small>{citation.evidence_summary || citation.finding || citation.relevance || "No evidence summary recorded"}</small>
              <small>{[citation.provider, citation.confidence, citation.publish_date].filter(Boolean).map(formatLabel).join(" · ")}</small>
            </div>
            {href && <b>↗</b>}
          </>;
          return href
            ? <a href={href} target="_blank" rel="noopener noreferrer" key={citation.citation_id || href}>{content}</a>
            : <article className="citation-unlinked" key={citation.citation_id || index}>{content}</article>;
        }) : <p className="empty-proof">No citations are present in the governed state. Kevaro does not fabricate evidence.</p>}
      </div>
      {!!gaps.length && <div className="evidence-gaps">
        <small>OPEN EVIDENCE GAPS</small><p>{gaps.join(" · ")}</p>
      </div>}
    </div>
  );
}
