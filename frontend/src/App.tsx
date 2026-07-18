import { Route, Routes } from 'react-router-dom'
import { PublicLayout } from './components/layout/PublicLayout'
import { AdminLayout } from './components/layout/AdminLayout'
import { PortalLayout } from './components/layout/PortalLayout'
import { PortalShell } from './components/layout/PortalShell'
import { Home } from './pages/public/Home'
import { Features } from './pages/public/Features'
import { Pricing } from './pages/public/Pricing'
import { About } from './pages/public/About'
import { Contact } from './pages/public/Contact'
import { TenantsList } from './pages/admin/TenantsList'
import { NewTenantWizard } from './pages/admin/NewTenantWizard'
import { TenantDetail } from './pages/admin/TenantDetail'
import { PortalHome } from './pages/portal/PortalHome'
import { Overview } from './pages/portal/Overview'
import { Bookings } from './pages/portal/Bookings'
import { Calls } from './pages/portal/Calls'
import { Services } from './pages/portal/Services'
import { Settings } from './pages/portal/Settings'

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route index element={<Home />} />
        <Route path="features" element={<Features />} />
        <Route path="pricing" element={<Pricing />} />
        <Route path="about" element={<About />} />
        <Route path="contact" element={<Contact />} />
      </Route>

      {/* Client portal: picker, then the per-business app-shell */}
      <Route path="portal" element={<PortalLayout />}>
        <Route index element={<PortalHome />} />
      </Route>
      <Route path="portal/:slug" element={<PortalShell />}>
        <Route index element={<Overview />} />
        <Route path="bookings" element={<Bookings />} />
        <Route path="calls" element={<Calls />} />
        <Route path="services" element={<Services />} />
        <Route path="settings" element={<Settings />} />
      </Route>

      {/* Internal admin (no auth) */}
      <Route path="admin" element={<AdminLayout />}>
        <Route index element={<TenantsList />} />
        <Route path="new" element={<NewTenantWizard />} />
        <Route path="tenants/:slug" element={<TenantDetail />} />
      </Route>
    </Routes>
  )
}
