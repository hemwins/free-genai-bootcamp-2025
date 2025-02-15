import { useEffect, useState } from 'react'
import StudyActivity from '@/components/StudyActivity'
import { getStudyActivities, ActivityCard } from '@/services/api'


export default function StudyActivities() {
  const [activities, setActivities] = useState<ActivityCard[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getStudyActivities()
      .then(data => {
        setActivities(data)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return <div className="text-center">Loading study activities...</div>
  }

  if (error) {
    return <div className="text-red-500">Error: {error}</div>
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {activities.map((activity) => (
        <StudyActivity key={activity.id} activity={activity} />
      ))}
    </div>
  )
}