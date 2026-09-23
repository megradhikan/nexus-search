import { useEffect, useRef } from 'react'

export default function SearchBar({ value, onChange }) {
  const ref = useRef(null)
  useEffect(() => { ref.current?.focus() }, [])

  return (
    <input
      ref={ref}
      className="search-bar"
      type="text"
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder="Search across GitHub and Notion..."
    />
  )
}
