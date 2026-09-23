const EXAMPLES = [
  'retry logic with exponential backoff',
  'authentication token expiry handling',
]

export default function EmptyState({ onSelect }) {
  return (
    <div className="empty-state">
      <p>Search across your GitHub repos and Notion workspace.</p>
      <div className="example-chips">
        {EXAMPLES.map(q => (
          <button key={q} className="chip" onClick={() => onSelect(q)}>{q}</button>
        ))}
      </div>
    </div>
  )
}
