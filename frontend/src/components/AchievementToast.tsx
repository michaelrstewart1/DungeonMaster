import { useState, useEffect, useRef } from 'react'

export interface Achievement {
  id: string
  title: string
  description: string
  icon: string
}

export interface AchievementToastProps {
  achievement: Achievement
  onDismiss: () => void
}

/**
 * Toast notification for achievement unlocks.
 * Slides in from top-right, auto-dismisses after 5 seconds.
 */
export function AchievementToast({ achievement, onDismiss }: AchievementToastProps) {
  const [exiting, setExiting] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  useEffect(() => {
    timerRef.current = setTimeout(() => {
      setExiting(true)
      setTimeout(onDismiss, 300)
    }, 5000)

    return () => clearTimeout(timerRef.current)
  }, [onDismiss])

  const handleClose = () => {
    clearTimeout(timerRef.current)
    setExiting(true)
    setTimeout(onDismiss, 300)
  }

  return (
    <div className={`achievement-toast ${exiting ? 'achievement-toast-exit' : ''}`}>
      <div className="achievement-toast-icon">{achievement.icon}</div>
      <div className="achievement-toast-content">
        <div className="achievement-toast-title">{achievement.title}</div>
        <div className="achievement-toast-description">{achievement.description}</div>
      </div>
      <button
        className="achievement-toast-close"
        onClick={handleClose}
        aria-label="Dismiss achievement"
      >
        ×
      </button>
    </div>
  )
}

/**
 * Check if new achievements were unlocked based on game state.
 * Returns array of newly unlocked achievements.
 */
export function checkAchievements(
  messages: Array<{ role: string; text: string }>,
  turnCount: number,
  sceneVisitCount?: number,
  customEvents?: Record<string, boolean>
): Achievement[] {
  const unlocked: Achievement[] = []
  const customFlags = customEvents || {}

  // First Steps: First action taken
  if (turnCount === 1) {
    unlocked.push({
      id: 'first-steps',
      title: 'First Steps',
      description: 'Take your first action',
      icon: '👣',
    })
  }

  // Nat 20!: Natural 20 rolled
  if (customFlags['natural20']) {
    unlocked.push({
      id: 'nat-20',
      title: 'Nat 20!',
      description: 'Roll a natural 20',
      icon: '✨',
    })
  }

  // Critical Fail: Natural 1 rolled
  if (customFlags['naturalOne']) {
    unlocked.push({
      id: 'critical-fail',
      title: 'Critical Fail',
      description: 'Roll a natural 1',
      icon: '💥',
    })
  }

  // Chatty: 10+ messages sent
  if (messages.length >= 10) {
    unlocked.push({
      id: 'chatty',
      title: 'Chatty',
      description: 'Send 10+ messages',
      icon: '💬',
    })
  }

  // Veteran: 25+ turns taken
  if (turnCount >= 25) {
    unlocked.push({
      id: 'veteran',
      title: 'Veteran',
      description: 'Complete 25+ turns',
      icon: '⚔️',
    })
  }

  // Explorer: Visited 3+ scenes
  if ((sceneVisitCount || 0) >= 3) {
    unlocked.push({
      id: 'explorer',
      title: 'Explorer',
      description: 'Visit 3+ different scenes',
      icon: '🗺️',
    })
  }

  // Dragon Slayer: Defeated a dragon
  if (customFlags['defeatedDragon']) {
    unlocked.push({
      id: 'dragon-slayer',
      title: 'Dragon Slayer',
      description: 'Defeat a dragon',
      icon: '🐉',
    })
  }

  // Smooth Talker: Successful persuasion
  if (customFlags['successfulPersuasion']) {
    unlocked.push({
      id: 'smooth-talker',
      title: 'Smooth Talker',
      description: 'Successfully persuade an NPC',
      icon: '🎭',
    })
  }

  return unlocked
}
