import React, { useState, useEffect } from 'react';
import { Card, CardContent, Typography, Box, Button, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, Chip, IconButton, Tooltip, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, FormControl, InputLabel, Select, MenuItem, Switch, FormControlLabel }
  from '@mui/material';
import { Settings as SettingsIcon, Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon, AlertCircle as AlertCircleIcon, Refresh as RefreshIcon }
  from '@mui/icons-material';
import axios from 'axios';

const ToolManagement = () => {
  const [tools, setTools] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [dialogMode, setDialogMode] = useState('add'); // 'add' or 'edit'
  const [currentTool, setCurrentTool] = useState({});

  // 获取工具列表
  const fetchTools = async () => {
    try {
      setLoading(true);
      setError('');

      const response = await axios.get(`${process.env.REACT_APP_API_URL}/tools`);
      setTools(response.data);
    } catch (err) {
      setError(`获取工具列表失败: ${err.message || '未知错误'}`);
    } finally {
      setLoading(false);
    }
  };

  // 组件加载时获取工具列表
  useEffect(() => {
    fetchTools();
  }, []);

  // 打开添加工具对话框
  const handleAddTool = () => {
    setDialogMode('add');
    setCurrentTool({
      name: '',
      description: '',
      endpoint: '',
      parameters: {},
      auth_required: true
    });
    setOpenDialog(true);
  };

  // 打开编辑工具对话框
  const handleEditTool = (tool) => {
    setDialogMode('edit');
    setCurrentTool({ ...tool });
    setOpenDialog(true);
  };

  // 删除工具
  const handleDeleteTool = async (toolId) => {
    if (window.confirm('确定要删除此工具吗？')) {
      try {
        setLoading(true);
        setError('');
        setSuccess('');

        await axios.delete(`${process.env.REACT_APP_API_URL}/tools/${toolId}`);
        setSuccess('工具已成功删除');
        fetchTools(); // 刷新工具列表
      } catch (err) {
        setError(`删除工具失败: ${err.message || '未知错误'}`);
      } finally {
        setLoading(false);
      }
    }
  };

  // 保存工具（添加或编辑）
  const handleSaveTool = async () => {
    try {
      setLoading(true);
      setError('');
      setSuccess('');

      if (dialogMode === 'add') {
        await axios.post(`${process.env.REACT_APP_API_URL}/tools`, currentTool);
        setSuccess('工具已成功添加');
      } else {
        await axios.put(`${process.env.REACT_APP_API_URL}/tools/${currentTool.id}`, currentTool);
        setSuccess('工具已成功更新');
      }

      setOpenDialog(false);
      fetchTools(); // 刷新工具列表
    } catch (err) {
      setError(`保存工具失败: ${err.message || '未知错误'}`);
    } finally {
      setLoading(false);
    }
  };

  // 处理工具属性变化
  const handleToolChange = (e) => {
    const { name, value, type, checked } = e.target;
    setCurrentTool(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  return (
    <div className="tool-management-container">
      <Typography variant="h4" component="h1" gutterBottom>
        工具管理
      </Typography>

      <Card className="card">
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
            <Typography variant="h6" component="h2">
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <SettingsIcon sx={{ mr: 2 }} />
                已注册工具
              </Box>
            </Typography>
            <Button
              variant="contained"
              color="primary"
              startIcon={<AddIcon />}
              onClick={handleAddTool}
              disabled={loading}
            >
              添加工具
            </Button>
          </Box>

          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchTools}
              disabled={loading}
            >
              刷新列表
            </Button>
          </Box>

          {loading ? (
            <Typography variant="body1" color="textSecondary" align="center" sx={{ py: 4 }}>
              加载中...
            </Typography>
          ) : tools.length === 0 ? (
            <Typography variant="body1" color="textSecondary" align="center" sx={{ py: 4 }}>
              暂无已注册的工具
            </Typography>
          ) : (
            <TableContainer component={Paper} sx={{ mb: 2 }}>
              <Table aria-label="tools table">
                <TableHead>
                  <TableRow>
                    <TableCell>名称</TableCell>
                    <TableCell>描述</TableCell>
                    <TableCell>端点</TableCell>
                    <TableCell>认证要求</TableCell>
                    <TableCell align="right">操作</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {tools.map((tool) => (
                    <TableRow key={tool.id}>
                      <TableCell>{tool.name}</TableCell>
                      <TableCell>{tool.description}</TableCell>
                      <TableCell>{tool.endpoint}</TableCell>
                      <TableCell>
                        <Chip
                          icon={tool.auth_required ? <CheckCircleIcon size="small" /> : <AlertCircleIcon size="small" />}
                          label={tool.auth_required ? '是' : '否'}
                          color={tool.auth_required ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="编辑">
                          <IconButton size="small" onClick={() => handleEditTool(tool)} disabled={loading}>
                            <EditIcon size="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="删除">
                          <IconButton size="small" onClick={() => handleDeleteTool(tool.id)} disabled={loading}>
                            <DeleteIcon size="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* 添加/编辑工具对话框 */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md">
        <DialogTitle>{dialogMode === 'add' ? '添加工具' : '编辑工具'}</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="名称"
            variant="outlined"
            margin="dense"
            name="name"
            value={currentTool.name || ''}
            onChange={handleToolChange}
            required
          />

          <TextField
            fullWidth
            label="描述"
            variant="outlined"
            margin="dense"
            name="description"
            value={currentTool.description || ''}
            onChange={handleToolChange}
            multiline
            rows={2}
          />

          <TextField
            fullWidth
            label="端点 URL"
            variant="outlined"
            margin="dense"
            name="endpoint"
            value={currentTool.endpoint || ''}
            onChange={handleToolChange}
            required
          />

          <FormControlLabel
            control=
            <Switch
              name="auth_required"
              checked={currentTool.auth_required || false}
              onChange={handleToolChange}
            />
            label="需要认证"
            margin="dense"
          />

          <TextField
            fullWidth
            label="参数 (JSON格式)"
            variant="outlined"
            margin="dense"
            name="parameters"
            value={typeof currentTool.parameters === 'object' ? JSON.stringify(currentTool.parameters) : currentTool.parameters || ''}
            onChange={(e) => {
              try {
                const value = e.target.value;
                if (value) {
                  const params = JSON.parse(value);
                  setCurrentTool(prev => ({
                    ...prev,
                    parameters: params
                  }));
                } else {
                  setCurrentTool(prev => ({
                    ...prev,
                    parameters: {}
                  }));
                }
              } catch (err) {
                // 不更新状态，保持之前的参数
              }
            }}
            multiline
            rows={3}
            helperText="例如: {\"param1\": \"value1\", \"param2\": 123}"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)} disabled={loading}>取消</Button>
          <Button
            variant="contained"
            color="primary"
            onClick={handleSaveTool}
            disabled={loading || !currentTool.name || !currentTool.endpoint}
          >
            {loading ? '保存中...' : '保存'}
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default ToolManagement;