import { createBrowserRouter, Navigate } from 'react-router-dom'
import ProLayout from '@/layouts/ProLayout'
import Pools from '@/pages/Pools'
import PoolDetail from '@/pages/Pools/Detail'
import Rules from '@/pages/Rules'
import RuleDetail from '@/pages/Rules/Detail'
import Simulators from '@/pages/Simulators'
import SimulatorDetail from '@/pages/Simulators/Detail'
import AgentLog from '@/pages/AgentLog'

const router = createBrowserRouter([
  {
    path: '/agent-log/:ruleId',
    element: <AgentLog />,
  },
  {
    path: '/agent-log/:ruleId/:stockCode',
    element: <AgentLog />,
  },
  {
    path: '/',
    element: <ProLayout />,
    children: [
      { index: true, element: <Navigate to="/rule" replace /> },
      {
        path: 'pool',
        children: [
          { index: true, element: <Pools /> },
          { path: ':id', element: <PoolDetail /> },
        ],
      },
      {
        path: 'rule',
        children: [
          { index: true, element: <Rules /> },
          { path: ':id', element: <RuleDetail /> },
          { path: ':id/pool/:poolId', element: <div>Rule Pool Detail</div> },
        ],
      },
      {
        path: 'simulator',
        children: [
          { index: true, element: <Simulators /> },
          { path: ':id', element: <SimulatorDetail /> },
        ],
      },
    ],
  },
])

export default router
