const API_BASE = import.meta.env.VITE_API_URL || ''

export async function searchDocuments(query, topK = 10, sources = null) {
  const body = { query, top_k: topK }
  if (sources) body.sources = sources
  const res = await fetch(`${API_BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`Search failed: ${res.status}`)
  return res.json()
}

export async function submitFeedback(query, docId, chunkId, rank, signal) {
  await fetch(`${API_BASE}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query_text: query,
      doc_id: docId,
      chunk_id: chunkId,
      rank_at_feedback: rank,
      signal,
    }),
  })
}
