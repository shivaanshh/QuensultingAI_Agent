import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

/** Resets scroll to the top whenever the route changes, so navigating
 *  (especially from a footer link on a long page) never lands mid-page. */
export function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' as ScrollBehavior })
  }, [pathname])
  return null
}
