import SourceBadge from './SourceBadge'
import FeedbackButtons from './FeedbackButtons'

function highlightQuery(text, query) {
  if (!query) return text
  const parts = text.split(query)
  return parts.map((part, i) =>
    i < parts.length - 1
      ? [part, <mark key={i}>{query}</mark>]
      : part
  )
}

export default function ResultCard({ result, query }) {
  const isHybrid = result.retrieval_sources.includes('bm25') && result.retrieval_sources.includes('dense')

  return (
    <div className="result-card">
      <div className="result-header">
        <span className="result-rank">{result.rank}</span>
        <a href={result.url} target="_blank" rel="noreferrer" className="result-title">
          {result.title || result.doc_id}
        </a>
        <SourceBadge source={result.source} />
        {isHybrid && <span className="hybrid-tag">Hybrid match</span>}
      </div>
      <p className="result-excerpt">{highlightQuery(result.excerpt, query)}</p>
      <div className="result-footer">
        <span className="result-score">{result.rrf_score.toFixed(4)}</span>
        <FeedbackButtons query={query} result={result} />
      </div>
    </div>
  )
}
