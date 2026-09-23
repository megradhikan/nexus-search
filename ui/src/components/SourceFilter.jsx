const FILTERS = ['All', 'GitHub', 'Notion']

export default function SourceFilter({ active, onFilterChange }) {
  return (
    <div className="source-filter">
      {FILTERS.map(f => (
        <button
          key={f}
          className={`filter-btn${(active === null && f === 'All') || active === f.toLowerCase() ? ' active' : ''}`}
          onClick={() => onFilterChange(f === 'All' ? null : f.toLowerCase())}
        >
          {f}
        </button>
      ))}
    </div>
  )
}
