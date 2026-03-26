import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { ProLayout } from '@ant-design/pro-components'
import { useGlobalStore } from '@/store'
import {
  FundOutlined,
  AlertOutlined,
  ExperimentOutlined,
} from '@ant-design/icons'

// 路由配置
const routes = [
  {
    path: '/pool',
    name: 'Pools',
    icon: <FundOutlined />,
  },
  {
    path: '/rule',
    name: 'Agents',
    icon: <AlertOutlined />,
  },
  {
    path: '/simulator',
    name: 'Simulators',
    icon: <ExperimentOutlined />,
  },
]

const ProLayoutWrapper = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const { collapsed, setCollapsed } = useGlobalStore()

  return (
    <ProLayout
      route={{
        path: '/',
        routes: routes,
      }}
      location={location}
      collapsed={collapsed}
      onCollapse={setCollapsed}
      navTheme="realDark"
      layout="mix"
      contentWidth="Fluid"
      fixSiderbar
      fixedHeader
      logo={false}
      title="Fintools"
      menuItemRender={(menuItemProps, defaultDom) => {
        return (
          <a
            onClick={(e) => {
              e.preventDefault()
              if (menuItemProps.path) {
                navigate(menuItemProps.path)
              }
            }}
          >
            {defaultDom}
          </a>
        )
      }}
    >
      <Outlet />
    </ProLayout>
  )
}

export default ProLayoutWrapper
