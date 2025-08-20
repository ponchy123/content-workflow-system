import React, { useState } from 'react';
import { Card, CardContent, Typography, Box, Button, TextField, FormControl, InputLabel, Select, MenuItem,
  Snackbar, Alert, Slider }
  from '@mui/material';
import { Database as DatabaseIcon, Send as SendIcon, CheckCircle as CheckCircleIcon }
  from '@mui/icons-material';

const ContentGeneration = ({ sendRequest }) => {
  const [topic, setTopic] = useState('');
  const [format, setFormat] = useState('');
  const [length, setLength] = useState('medium');
  const [requirements, setRequirements] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  // 处理表单提交
  const handleSubmit = async (e) => {
    e.preventDefault();

    // 验证表单
    if (!topic || !format) {
      setError('请填写主题和格式');
      return;
    }

    try {
      setLoading(true);
      setError('');
      setSuccess('');

      // 发送请求到调度器
      await sendRequest('generate_content', {
        topic,
        format,
        length,
        requirements: requirements || {}
      });

      setSuccess('内容生成请求已发送，请到任务状态页面查看进度');

      // 重置表单
      setTopic('');
      setFormat('');
      setLength('medium');
      setRequirements('');
    } catch (err) {
      setError(`发送请求失败: ${err.message || '未知错误'}`);
    } finally {
      setLoading(false);
    }
  };

  // 长度选项对应的值
  const lengthOptions = [
    { value: 'short', label: '短 (约200字)' },
    { value: 'medium', label: '中 (约500字)' },
    { value: 'long', label: '长 (约1000字)' }
  ];

  return (
    <div className="content-generation-container">
      <Typography variant="h4" component="h1" gutterBottom>
        内容生成
      </Typography>

      <Card className="card">
        <CardContent>
          <Typography variant="h6" component="h2" gutterBottom>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <DatabaseIcon sx={{ mr: 2 }} />
              发送内容生成请求
            </Box>
          </Typography>

          <form onSubmit={handleSubmit} className="generation-form">
            <TextField
              fullWidth
              label="主题"
              variant="outlined"
              className="form-group"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              required
            />

            <FormControl fullWidth className="form-group">
              <InputLabel id="format-label">格式</InputLabel>
              <Select
                labelId="format-label"
                value={format}
                label="格式"
                onChange={(e) => setFormat(e.target.value)}
                required
              >
                <MenuItem value="article">文章</MenuItem>
                <MenuItem value="summary">摘要</MenuItem>
                <MenuItem value="report">报告</MenuItem>
                <MenuItem value="email">邮件</MenuItem>
                <MenuItem value="social_media">社交媒体帖子</MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth className="form-group">
              <InputLabel id="length-label">长度</InputLabel>
              <Select
                labelId="length-label"
                value={length}
                label="长度"
                onChange={(e) => setLength(e.target.value)}
              >
                {lengthOptions.map(option => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="额外要求 (可选)"
              variant="outlined"
              className="form-group"
              multiline
              rows={4}
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              placeholder="例如：风格正式、包含特定关键词、面向特定受众等"
            />

            <Button
              variant="contained"
              color="success"
              type="submit"
              startIcon={loading ? <CheckCircleIcon /> : <SendIcon />}
              disabled={loading}
              sx={{ mt: 2 }}
            >
              {loading ? '发送中...' : '发送请求'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError('')}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setError('')} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!success}
        autoHideDuration={6000}
        onClose={() => setSuccess('')}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setSuccess('')} severity="success" sx={{ width: '100%' }}>
          {success}
        </Alert>
      </Snackbar>
    </div>
  );
};

export default ContentGeneration;