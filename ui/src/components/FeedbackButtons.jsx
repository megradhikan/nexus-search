import { useState } from 'react'
import { submitFeedback } from '../api'

export default function FeedbackButtons({ query, result }) {
  const [done, setDone] = useState(false)
  const [thanks, setThanks] = useState(false)

  const handleClick = async (signal) => {
    if (done) return
    setDone(true)
    await submitFeedback(query, result.doc_id, result.chunk_id, result.rank, signal)
    setThanks(true)
    setTimeout(() => setThanks(false), 1500)
  }

  if (thanks) return <span className="feedback-thanks">Thanks!</span>

  return (
    <div className="feedback-buttons">
      <button onClick={() => handleClick('positive')} disabled={done}>&#128077;</button>
      <button onClick={() => handleClick('negative')} disabled={done}>&#128078;</button>
    </div>
  )
}
