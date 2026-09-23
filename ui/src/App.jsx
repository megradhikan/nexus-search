import { useState, useCallback, useEffect } from 'react'
import debounce from 'lodash.debounce'
import { searchDocuments } from './api'
import SearchBar from './components/SearchBar'
import ResultCard from './components/ResultCard'
import SourceFilter from './components/SourceFilter'
import LatencyBadge from './components/LatencyBadge'
import EmptyState from './components/EmptyState'
import LoadingSpinner from './components/LoadingSpinner'
import './App.css'

export default function App() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [latency, setLatency] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeSource, setActiveSource] = useState(null)

  const doSearch = useCallback(
    debounce(async (q, source) => {
      if (q.length < 3) {
        setResults([])
        setLatency(null)
        return
      }
      setLoading(true)
      setError(null)
      try {
        const data = await searchDocuments(q, 10, source ? [source] : null)
        setResults(data.results)
        setLatency(data.latency_ms)
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }, 300),
    []
  )

  useEffect(() => {
    doSearch(query, activeSource)
  }, [query, activeSource])

  return (
    <div className="app">
      <LatencyBadge latency={latency} />
      <div className="search-container">
        <h1 className="logo">NexusSearch</h1>
        <SearchBar value={query} onChange={setQuery} />
        <SourceFilter active={activeSource} onFilterChange={setActiveSource} />
      </div>
      <div className="results-container">
        {loading && <LoadingSpinner />}
        {error && <p className="error">{error}</p>}
        {!loading && !error && query.length < 3 && <EmptyState onSelect={setQuery} />}
        {!loading && !error && results.map(r => (
          <ResultCard key={r.chunk_id} result={r} query={query} />
        ))}
      </div>
    </div>
  )
}
