import React, { useEffect, useRef } from 'react';
import { Card, CardContent, Typography, Box, Button, Grid, Container }
  from '@mui/material';
import { BarChart as BarChartIcon, FileText as FileTextIcon, Database as DatabaseIcon,
  CheckCircle as CheckCircleIcon, Send as SendIcon, ArrowRight as ArrowRightIcon }
  from '@mui/icons-material';
import { Link } from 'react-router-dom';

const Home = () => {
  // 创建引用以便添加动画
  const homeRef = useRef(null);

  // 页面加载时添加动画
  useEffect(() => {
    if (homeRef.current) {
      homeRef.current.classList.add('fade-in');
    }
  }, []);

  // 卡片数据
  const cards = [
    {
      title: '数据分析',
      description: '发送数据分析请求，获取数据洞察和可视化结果。',
      icon: <BarChartIcon className="card-icon" />,
      color: 'primary',
      path: '/data-analysis',
      iconBg: 'rgba(33, 150, 243, 0.1)',
    },
    {
      title: '内容生成',
      description: '基于指定主题和格式，生成高质量内容。',
      icon: <DatabaseIcon className="card-icon" />,
      color: 'success',
      path: '/content-generation',
      iconBg: 'rgba(76, 175, 80, 0.1)',
    },
    {
      title: '任务状态',
      description: '查看所有任务的进度和结果。',
      icon: <CheckCircleIcon className="card-icon" />,
      color: 'warning',
      path: '/task-status',
      iconBg: 'rgba(255, 152, 0, 0.1)',
    },
    {
      title: '工具管理',
      description: '管理已注册的工具和服务。',
      icon: <FileTextIcon className="card-icon" />,
      color: 'secondary',
      path: '/tool-management',
      iconBg: 'rgba(156, 39, 176, 0.1)',
    },
  ];

  return (
    <Container maxWidth="lg" ref={homeRef} className="home-container">
      <Box sx={{ mt: 8, mb: 10, textAlign: 'center' }}>
        <Typography variant="h3" component="h1" gutterBottom className="main-title">
          欢迎使用 A2A+MCP 智能体交互平台
        </Typography>
        <Typography variant="h6" paragraph className="subtitle">
          这是一个与多智能体系统交互的用户界面，您可以发送数据分析请求、内容生成请求，并查看任务进度和结果。
        </Typography>
      </Box>

      <Grid container spacing={{ xs: 4, md: 6 }} className="cards-grid">
        {cards.map((card, index) => (
          <Grid item xs={12} sm={6} md={6} lg={3} key={index} className="card-item fade-in" style={{ animationDelay: `${index * 0.1}s` }}>
            <Card className="card" sx={{ height: '100%', display: 'flex', flexDirection: 'column', transition: 'all 0.3s ease' }}>
              <CardContent className="card-content">
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                  <Box className="icon-container" sx={{ bgcolor: card.iconBg, p: 2, borderRadius: '50%', mr: 3 }}>
                    {card.icon}
                  </Box>
                  <Typography variant="h5" component="h2" className="card-title">
                    {card.title}
                  </Typography>
                </Box>
                <Typography variant="body1" paragraph className="card-description">
                  {card.description}
                </Typography>
                <Button
                  variant="contained"
                  color={card.color}
                  component={Link}
                  to={card.path}
                  endIcon={<ArrowRightIcon />}
                  sx={{ mt: 3, textTransform: 'none', fontWeight: 500, borderRadius: 2, px: 4 }}
                  className="action-button"
                >
                  {card.title === '数据分析' && '开始分析'}
                  {card.title === '内容生成' && '生成内容'}
                  {card.title === '任务状态' && '查看任务'}
                  {card.title === '工具管理' && '管理工具'}
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Box sx={{ mt: 12, textAlign: 'center' }} className="call-to-action fade-in" style={{ animationDelay: '0.5s' }}>
        <Typography variant="h5" paragraph>
          准备好开始使用了吗？
        </Typography>
        <Button
          variant="contained"
          color="primary"
          size="large"
          component={Link}
          to="/register"
          sx={{ textTransform: 'none', fontWeight: 500, borderRadius: 2, px: 6, py: 1.5 }}
        >
          立即注册
        </Button>
      </Box>
    </Container>
  );
};

export default Home;