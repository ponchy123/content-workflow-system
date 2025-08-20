import React, { useState, useEffect, useContext } from 'react';
import { Routes, Route, Link, Navigate } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Button, Container, Box, Drawer, List, ListItem, ListItemText, ListItemIcon } from '@mui/material';
import { AuthProvider, AuthContext } from './contexts/AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import { BarChart as BarChartIcon, FileText as FileTextIcon, Database as DatabaseIcon, Settings as SettingsIcon,
  Menu as MenuIcon, Send as SendIcon, CheckCircle as CheckCircleIcon, AlertCircle as AlertCircleIcon }
  from '@mui/icons-material';
import axios from 'axios';
import io from 'socket.io-client';

// 懒加载其他页面组件
const Home = React.lazy(() => import('./pages/Home'));
const DataAnalysis = React.lazy(() => import('./pages/DataAnalysis'));
const ContentGeneration = React.lazy(() => import('./pages/ContentGeneration'));
const TaskStatus = React.lazy(() => import('./pages/TaskStatus'));
const ToolManagement = React.lazy(() => import('./pages/ToolManagement'));
const NotFound = React.lazy(() => import('./pages/NotFound'));

import './App.css';

const AppContent = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [tasks, setTasks] = useState([]);
  const [socket, setSocket] = useState(null);
  const [menuItems, setMenuItems] = useState([
    { text: '首页', icon: <FileTextIcon />, path: '/' },
    { text: '数据分析', icon: <BarChartIcon />, path: '/data-analysis' },
    { text: '内容生成', icon: <DatabaseIcon />, path: '/content-generation' },
    { text: '任务状态', icon: <CheckCircleIcon />, path: '/task-status' },
    { text: '工具管理', icon: <SettingsIcon />, path: '/tool-management' },
  ]);

  const { currentUser, logout } = useContext(AuthContext);

  // 根据认证状态更新菜单项
  useEffect(() => {
    if (currentUser) {
      setMenuItems([
        { text: '首页', icon: <FileTextIcon />, path: '/' },
        { text: '数据分析', icon: <BarChartIcon />, path: '/data-analysis' },
        { text: '内容生成', icon: <DatabaseIcon />, path: '/content-generation' },
        { text: '任务状态', icon: <CheckCircleIcon />, path: '/task-status' },
        { text: '工具管理', icon: <SettingsIcon />, path: '/tool-management' },
      ]);
    } else {
      setMenuItems([
        { text: '首页', icon: <FileTextIcon />, path: '/' },
      ]);
    }
  }, [currentUser]);

  // 初始化Socket.io连接
  useEffect(() => {
    const newSocket = io(process.env.REACT_APP_WS_URL);
    setSocket(newSocket);

    // 监听任务状态更新
    newSocket.on('task_update', (task) => {
      setTasks(prevTasks => {
        const index = prevTasks.findIndex(t => t.id === task.id);
        if (index !== -1) {
          const updatedTasks = [...prevTasks];
          updatedTasks[index] = task;
          return updatedTasks;
        } else {
          return [...prevTasks, task];
        }
      });
    });

    return () => newSocket.disconnect();
  }, []);

  // 处理移动端菜单切换
  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  // 发送请求到调度器
  const sendRequest = async (requestType, data) => {
    try {
      const response = await axios.post(`${process.env.REACT_APP_API_URL}/requests`, {
        type: requestType,
        data
      });

      // 创建新任务
      const newTask = {
        id: response.data.request_id,
        type: requestType,
        status: 'pending',
        createdAt: new Date().toISOString(),
        data
      };

      setTasks(prevTasks => [...prevTasks, newTask]);
      return response.data;
    } catch (error) {
      console.error('发送请求失败:', error);
      throw error;
    }
  };

  // 抽屉内容
  const drawerContent = (
    <div>
      <Toolbar />
      <List>
        {menuItems.map((item) => (
          <ListItem button key={item.text} component={Link} to={item.path} onClick={() => setMobileOpen(false)}>
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>
    </div>
  );

  return (
    <div className="app-container">
      {/* 顶部应用栏 */}
      <AppBar position="fixed" className="app-bar">
        <Toolbar>
          <Button
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            className="menu-button"
          >
            <MenuIcon />
          </Button>
          <Typography variant="h6" className="app-title">
            A2A+MCP 智能体交互平台
          </Typography>
          <Box className="app-bar-buttons">
        {currentUser ? (
          <>            
            <Typography variant="body2" color="inherit" sx={{ mr: 2 }}>
              欢迎, {currentUser.username}
            </Typography>
            <Button color="inherit" onClick={logout}>
              登出
            </Button>
          </>
        ) : (
          <>            
            <Button color="inherit" component={Link} to="/login">
              登录
            </Button>
            <Button color="inherit" component={Link} to="/register">
              注册
            </Button>
          </>
        )}
      </Box>
        </Toolbar>
      </AppBar>

      {/* 移动端抽屉 */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{ keepMounted: true }}
      >
        {drawerContent}
      </Drawer>

      {/* 桌面端侧边栏 */}
      <Drawer variant="permanent" className="desktop-drawer" hidden={window.innerWidth < 768}>
        {drawerContent}
      </Drawer>

      {/* 主内容区域 */}
      <main className="main-content">
        <Container maxWidth="lg" className="content-container">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={currentUser ? <Navigate to="/" /> : <Login />} />
            <Route path="/register" element={currentUser ? <Navigate to="/" /> : <Register />} />
            <Route path="/data-analysis" element={currentUser ? <DataAnalysis sendRequest={sendRequest} /> : <Navigate to="/login" />} />
            <Route path="/content-generation" element={currentUser ? <ContentGeneration sendRequest={sendRequest} /> : <Navigate to="/login" />} />
            <Route path="/task-status" element={currentUser ? <TaskStatus tasks={tasks} /> : <Navigate to="/login" />} />
            <Route path="/tool-management" element={currentUser ? <ToolManagement /> : <Navigate to="/login" />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Container>
      </main>
    </div>
  );
};

// 包装应用并提供认证上下文
const App = () => (
  <AuthProvider>
    <AppContent />
  </AuthProvider>
);

export default App;