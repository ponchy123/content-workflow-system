import React, { useState } from 'react';
import { Card, CardContent, Typography, Box, Button, TextField, FormControl, InputLabel, Select, MenuItem,
  Snackbar, Alert }
  from '@mui/material';
import { BarChart as BarChartIcon, Send as SendIcon, CheckCircle as CheckCircleIcon }
  from '@mui/icons-material';

const DataAnalysis = ({ sendRequest }) => {
  const [dataset, setDataset] = useState('');
  const [analysisType, setAnalysisType] = useState('');
  const [parameters, setParameters] = useState({});
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  // 处理表单提交
  const handleSubmit = async (e) => {
    e.preventDefault();

    // 验证表单
    if (!dataset || !analysisType) {
      setError('请填写数据集和分析类型');
      return;
    }

    try {
      setLoading(true);
      setError('');
      setSuccess('');

      // 发送请求到调度器
      await sendRequest('analyze_data', {
        dataset,
        analysis_type: analysisType,
        parameters
      });

      setSuccess('数据分析请求已发送，请到任务状态页面查看进度');

      // 重置表单
      setDataset('');
      setAnalysisType('');
      setParameters({});
    } catch (err) {
      setError(`发送请求失败: ${err.message || '未知错误'}`);
    } finally {
      setLoading(false);
    }
  };

  // 处理参数变化
  const handleParameterChange = (e) => {
    const { name, value } = e.target;
    setParameters(prev => ({ ...prev, [name]: value }));
  };

  return (
    <div className="data-analysis-container">
      <Typography variant="h4" component="h1" gutterBottom>
        数据分析
      </Typography>

      <Card className="card">
        <CardContent>
          <Typography variant="h6" component="h2" gutterBottom>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <BarChartIcon sx={{ mr: 2 }} />
              发送数据分析请求
            </Box>
          </Typography>

          <form onSubmit={handleSubmit} className="analysis-form">
            <FormControl fullWidth className="form-group">
              <InputLabel id="dataset-label">数据集</InputLabel>
              <Select
                labelId="dataset-label"
                value={dataset}
                label="数据集"
                onChange={(e) => setDataset(e.target.value)}
                required
              >
                <MenuItem value="sales_data">销售数据</MenuItem>
                <MenuItem value="user_activity">用户活动数据</MenuItem>
                <MenuItem value="market_trends">市场趋势数据</MenuItem>
                <MenuItem value="custom">自定义数据集</MenuItem>
              </Select>
            </FormControl>

            {dataset === 'custom' && (
              <TextField
                fullWidth
                label="自定义数据集URL"
                variant="outlined"
                className="form-group"
                value={parameters.datasetUrl || ''}
                name="datasetUrl"
                onChange={handleParameterChange}
                required
              />
            )}

            <FormControl fullWidth className="form-group">
              <InputLabel id="analysis-type-label">分析类型</InputLabel>
              <Select
                labelId="analysis-type-label"
                value={analysisType}
                label="分析类型"
                onChange={(e) => setAnalysisType(e.target.value)}
                required
              >
                <MenuItem value="trend_analysis">趋势分析</MenuItem>
                <MenuItem value="correlation_analysis">相关性分析</MenuItem>
                <MenuItem value="predictive_analysis">预测分析</MenuItem>
                <MenuItem value="segmentation">用户细分</MenuItem>
              </Select>
            </FormControl>

            {analysisType === 'predictive_analysis' && (
              <TextField
                fullWidth
                label="预测周期 (天)"
                variant="outlined"
                className="form-group"
                type="number"
                value={parameters.forecastDays || ''}
                name="forecastDays"
                onChange={handleParameterChange}
                required
                InputProps={{ inputProps: { min: 1 } }}
              />
            )}

            <Button
              variant="contained"
              color="primary"
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

export default DataAnalysis;