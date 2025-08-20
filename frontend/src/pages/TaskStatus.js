import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../contexts/AuthContext';

import { Card, CardContent, Typography, Box, List, ListItem, ListItemText, ListItemIcon, Chip,
  Divider, Button, IconButton, Tooltip }
  from '@mui/material';
import { CheckCircle as CheckCircleIcon, AlertCircle as AlertCircleIcon, Clock as ClockIcon,
  BarChart as BarChartIcon, Database as DatabaseIcon, FileText as FileTextIcon,
  Refresh as RefreshIcon, Download as DownloadIcon }
  from '@mui/icons-material';
import moment from 'moment';

const TaskStatus = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const { currentUser } = useContext(AuthContext);

  // 获取任务列表
  const fetchTasks = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${process.env.REACT_APP_API_URL}/tasks`);
      setTasks(response.data.tasks);
    } catch (error) {
      console.error('获取任务失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 组件挂载时获取任务
  useEffect(() => {
    if (currentUser) {
      fetchTasks();
    }
  }, [currentUser]);

  // 刷新任务
  const handleRefresh = () => {
    fetchTasks();
  };

  // 获取任务状态对应的图标和颜色

  // 获取任务状态对应的图标和颜色
  const getTaskStatusInfo = (status) => {
    switch (status) {
      case 'pending':
        return { icon: <ClockIcon />, color: 'warning', label: '处理中' };
      case 'success':
        return { icon: <CheckCircleIcon />, color: 'success', label: '成功' };
      case 'error':
        return { icon: <AlertCircleIcon />, color: 'error', label: '失败' };
      default:
        return { icon: <FileTextIcon />, color: 'default', label: '未知' };
    }
  };

  // 获取任务类型对应的图标
  const getTaskTypeIcon = (type) => {
    switch (type) {
      case 'analyze_data':
        return <BarChartIcon />;
      case 'generate_content':
        return <DatabaseIcon />;
      default:
        return <FileTextIcon />;
    }
  };

  // 格式化日期时间
  const formatDateTime = (dateString) => {
    return moment(dateString).format('YYYY-MM-DD HH:mm:ss');
  };

  return (
    <div className="task-status-container">
      <Typography variant="h4" component="h1" gutterBottom>
        任务状态
      </Typography>

      <Card className="card">
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" component="h2">
              所有任务
            </Typography>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={handleRefresh}
              disabled={loading}
            >
              {loading ? '刷新中...' : '刷新'}
            </Button>
          </Box>

          {loading ? (
            <Typography variant="body1" color="textSecondary" align="center" sx={{ py: 4 }}>
              加载中...
            </Typography>
          ) : tasks.length === 0 ? (
            <Typography variant="body1" color="textSecondary" align="center" sx={{ py: 4 }}>
              暂无任务记录
            </Typography>
          ) : (
            <List className="task-list">
              {tasks.map((task) => {
                const statusInfo = getTaskStatusInfo(task.status);
                return (
                  <React.Fragment key={task.id}>
                    <ListItem className={`task-item task-${task.status}`}>
                      <ListItemIcon sx={{ minWidth: 40 }}>
                        {getTaskTypeIcon(task.type)}
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                            <span>{task.type === 'analyze_data' ? '数据分析' : '内容生成'}</span>
                            <Chip
                              icon={statusInfo.icon}
                              label={statusInfo.label}
                              color={statusInfo.color}
                              size="small"
                            />
                          </Box>
                        }
                        secondary={
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="body2" color="textSecondary">
                              创建时间: {formatDateTime(task.createdAt)}
                            </Typography>
                            {task.data && (
                              <Typography variant="body2" mt={1}>
                                {task.type === 'analyze_data' ? (
                                  <>数据集: {task.data.dataset}, 分析类型: {task.data.analysis_type}</>
                                ) : (
                                  <>主题: {task.data.topic}, 格式: {task.data.format}</>
                                )}
                              </Typography>
                            )}
                            {task.result && (
                              <Box sx={{ mt: 1, p: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
                                <Typography variant="body2" fontWeight="medium">
                                  结果:
                                </Typography>
                                <Typography variant="body2" sx={{ mt: 1 }}>
                                  {typeof task.result === 'string' ? task.result : JSON.stringify(task.result)}
                                </Typography>
                                <Box sx={{ mt: 1, display: 'flex', justifyContent: 'flex-end' }}>
                                  <Tooltip title="下载结果">
                                    <IconButton size="small">
                                      <DownloadIcon size="small" />
                                    </IconButton>
                                  </Tooltip>
                                </Box>
                              </Box>
                            )}
                          </Box>
                        }
                      /ListItemText>
                    </ListItem>
                    <Divider />
                  </React.Fragment>
                );
              })}
            </List>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default TaskStatus;