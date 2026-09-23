export default function SourceBadge({ source }) {
  const styles = {
    github: { background: '#2d2d2d', color: '#e8e8e8' },
    notion: { background: '#3d3520', color: '#d4c47a' },
  }
  const style = styles[source] || { background: '#2a2a2a', color: '#e8e8e8' }
  return (
    <span className="source-badge" style={style}>
      {source.charAt(0).toUpperCase() + source.slice(1)}
    </span>
  )
}
