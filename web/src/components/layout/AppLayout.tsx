import React from 'react'
import { Layout } from 'antd'
import { Outlet } from 'react-router-dom'
import AppHeader from './AppHeader'
import AppSidebar from './AppSidebar'
import AppContent from './AppContent'
import { useAppStore } from '@/stores'
import './Layout.css'

const { Sider, Content } = Layout

const AppLayout: React.FC = () => {
  const { ui } = useAppStore()

  return (
    <Layout className="app-layout" style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={ui.sidebarCollapsed}
        width={280}
        className="app-sidebar"
        theme={ui.theme}
      >
        <AppSidebar />
      </Sider>
      
      <Layout>
        <AppHeader />
        <Content className="app-content">
          <AppContent>
            <Outlet />
          </AppContent>
        </Content>
      </Layout>
    </Layout>
  )
}

export default AppLayout