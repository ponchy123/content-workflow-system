import React from 'react';
import { Card, CardContent, Typography, Box, Button }
  from '@mui/material';
import { AlertCircle as AlertCircleIcon }
  from '@mui/icons-material';
import { Link } from 'react-router-dom';

const NotFound = () => {
  return (
    <div className="not-found-container">
      <Card className="card" sx={{ maxWidth: 500, margin: '0 auto' }}>
        <CardContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
            <AlertCircleIcon sx={{ fontSize: 64, color: 'error.main', mb: 2 }} />
            <Typography variant="h4" component="h1" gutterBottom>
              404 - 页面不存在
            </Typography>
            <Typography variant="body1" paragraph>
              抱歉，您访问的页面不存在或已被移除。
            </Typography>
            <Button
              variant="contained"
              color="primary"
              component={Link}
              to="/"
              sx={{ mt: 2 }}
            >
              返回首页
            </Button>
          </Box>
        </CardContent>
      </Card>
    </div>
  );
};

export default NotFound;