export default function LatencyBadge({ latency }) {
  if (latency === null) return null
  const color = latency < 200 ? '#4ade80' : latency < 500 ? '#facc15' : '#f87171'
  return (
    <div className="latency-badge" style={{ color }}>
      {Math.round(latency)}ms
    </div>
  )
}
