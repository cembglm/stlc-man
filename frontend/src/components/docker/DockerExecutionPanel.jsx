import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Alert,
  CircularProgress,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Memory as MemoryIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import axios from 'axios';

const DockerExecutionPanel = () => {
  // State
  const [testCode, setTestCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [robotType, setRobotType] = useState('generic');
  const [executionMode, setExecutionMode] = useState('standard'); // standard, robot, custom
  const [additionalPackages, setAdditionalPackages] = useState('');
  const [timeout, setTimeout] = useState(300);
  
  // Docker status
  const [dockerAvailable, setDockerAvailable] = useState(false);
  const [dockerImages, setDockerImages] = useState([]);
  const [containerStatus, setContainerStatus] = useState({});
  
  // Execution state
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);
  const [error, setError] = useState(null);
  
  // Available options
  const [availableRobots, setAvailableRobots] = useState([]);
  const [supportedLanguages, setSupportedLanguages] = useState([]);

  // Load Docker status on mount
  useEffect(() => {
    checkDockerStatus();
    loadAvailableOptions();
  }, []);

  const checkDockerStatus = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/docker-execution/status');
      setDockerAvailable(response.data.docker_available);
      setDockerImages(response.data.images || []);
      setContainerStatus(response.data.container_status || {});
    } catch (error) {
      console.error('Failed to check Docker status:', error);
      setDockerAvailable(false);
    }
  };

  const loadAvailableOptions = async () => {
    try {
      const [robotsRes, languagesRes] = await Promise.all([
        axios.get('http://localhost:8000/api/docker-execution/available-robots'),
        axios.get('http://localhost:8000/api/docker-execution/supported-languages')
      ]);
      
      setAvailableRobots(robotsRes.data.robot_types || []);
      setSupportedLanguages(languagesRes.data.languages || []);
    } catch (error) {
      console.error('Failed to load options:', error);
    }
  };

  const handleExecute = async () => {
    if (!testCode.trim()) {
      setError('Please enter test code');
      return;
    }

    setIsExecuting(true);
    setError(null);
    setExecutionResult(null);

    try {
      let endpoint = '';
      let payload = {};

      if (executionMode === 'robot') {
        endpoint = '/api/docker-execution/execute-robot-simulation';
        payload = {
          test_code: testCode,
          robot_type: robotType,
          simulation_config: {
            precision: 'high',
            simulation_speed: 1.0
          }
        };
      } else {
        endpoint = '/api/docker-execution/execute';
        payload = {
          test_code: testCode,
          language: language,
          timeout: timeout
        };
        
        if (additionalPackages.trim()) {
          payload.additional_packages = additionalPackages
            .split(',')
            .map(pkg => pkg.trim())
            .filter(pkg => pkg);
        }
      }

      const response = await axios.post(`http://localhost:8000${endpoint}`, payload, {
        timeout: (timeout + 30) * 1000 // Add buffer to timeout
      });

      setExecutionResult(response.data);
    } catch (error) {
      console.error('Execution error:', error);
      setError(error.response?.data?.detail || error.message || 'Execution failed');
    } finally {
      setIsExecuting(false);
    }
  };

  const loadExampleCode = (mode) => {
    const examples = {
      python: `# Simple Python Test
print("Running tests...")

def test_addition():
    assert 2 + 2 == 4
    print("✅ Addition test passed")

def test_multiplication():
    assert 3 * 4 == 12
    print("✅ Multiplication test passed")

test_addition()
test_multiplication()
print("\\n✅ All tests completed!")`,
      
      robot: `# Robot Arm Movement Test
print("🤖 Starting robot arm test...")

# Move to home position
success, pos = robot.move_to_position([0, 0, 0])
print(f"Home position: {pos}")

# Test workspace positions
positions = [
    [0.5, 0.3, 0.2],
    [0.8, 0.4, 0.3],
    [0.6, -0.2, 0.25]
]

for i, pos in enumerate(positions, 1):
    success, position = robot.move_to_position(pos)
    print(f"Position {i}: {'✅' if success else '❌'} - {position}")

print("\\n✅ Robot test completed!")`,
      
      packages: `# Test with NumPy and Pandas
import numpy as np
import pandas as pd

print("Testing NumPy...")
arr = np.array([1, 2, 3, 4, 5])
print(f"Array: {arr}")
print(f"Mean: {np.mean(arr)}")

print("\\nTesting Pandas...")
df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
print(df)
print("\\n✅ Package test completed!")`
    };

    setTestCode(examples[mode] || examples.python);
    
    if (mode === 'robot') {
      setExecutionMode('robot');
    } else if (mode === 'packages') {
      setAdditionalPackages('numpy,pandas');
      setExecutionMode('standard');
    } else {
      setExecutionMode('standard');
      setAdditionalPackages('');
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <MemoryIcon sx={{ mr: 1, fontSize: 32, color: 'primary.main' }} />
            <Typography variant="h5" component="h2">
              Docker-Based Test Execution
            </Typography>
            <Box sx={{ flexGrow: 1 }} />
            <Tooltip title="Refresh Docker status">
              <IconButton onClick={checkDockerStatus} size="small">
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>

          {/* Docker Status */}
          <Alert 
            severity={dockerAvailable ? "success" : "error"} 
            sx={{ mb: 2 }}
            icon={dockerAvailable ? <CheckCircleIcon /> : <ErrorIcon />}
          >
            Docker is {dockerAvailable ? 'available' : 'not available'}
            {dockerAvailable && ` - ${dockerImages.length} images available`}
          </Alert>

          {/* Execution Mode Selection */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              Execution Mode
            </Typography>
            <Grid container spacing={1}>
              <Grid item>
                <Chip
                  label="Standard Test"
                  color={executionMode === 'standard' ? 'primary' : 'default'}
                  onClick={() => setExecutionMode('standard')}
                  sx={{ cursor: 'pointer' }}
                />
              </Grid>
              <Grid item>
                <Chip
                  label="Robot Simulation"
                  color={executionMode === 'robot' ? 'primary' : 'default'}
                  onClick={() => setExecutionMode('robot')}
                  sx={{ cursor: 'pointer' }}
                />
              </Grid>
            </Grid>
          </Box>

          {/* Configuration */}
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <SettingsIcon sx={{ mr: 1 }} />
              <Typography>Configuration</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                {executionMode === 'robot' ? (
                  <Grid item xs={12}>
                    <FormControl fullWidth>
                      <InputLabel>Robot Type</InputLabel>
                      <Select
                        value={robotType}
                        onChange={(e) => setRobotType(e.target.value)}
                        label="Robot Type"
                      >
                        {availableRobots.map((robot) => (
                          <MenuItem key={robot.id} value={robot.id}>
                            {robot.name} ({robot.dof} DOF)
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                ) : (
                  <>
                    <Grid item xs={12} md={6}>
                      <FormControl fullWidth>
                        <InputLabel>Language</InputLabel>
                        <Select
                          value={language}
                          onChange={(e) => setLanguage(e.target.value)}
                          label="Language"
                        >
                          {supportedLanguages.map((lang) => (
                            <MenuItem key={lang.id} value={lang.id}>
                              {lang.name}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Additional Packages"
                        value={additionalPackages}
                        onChange={(e) => setAdditionalPackages(e.target.value)}
                        placeholder="numpy,pandas,requests"
                        helperText="Comma-separated package names"
                      />
                    </Grid>
                  </>
                )}
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Timeout (seconds)"
                    value={timeout}
                    onChange={(e) => setTimeout(parseInt(e.target.value))}
                    inputProps={{ min: 30, max: 600 }}
                  />
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>

          {/* Example Code Buttons */}
          <Box sx={{ mt: 2, mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Load Example:
            </Typography>
            <Grid container spacing={1}>
              <Grid item>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => loadExampleCode('python')}
                >
                  Simple Python
                </Button>
              </Grid>
              <Grid item>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => loadExampleCode('robot')}
                >
                  Robot Simulation
                </Button>
              </Grid>
              <Grid item>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => loadExampleCode('packages')}
                >
                  With Packages
                </Button>
              </Grid>
            </Grid>
          </Box>

          {/* Test Code Editor */}
          <TextField
            fullWidth
            multiline
            rows={15}
            label="Test Code"
            value={testCode}
            onChange={(e) => setTestCode(e.target.value)}
            placeholder="Enter your test code here..."
            sx={{ mb: 2, fontFamily: 'monospace' }}
            InputProps={{
              sx: { fontFamily: 'Courier New, monospace', fontSize: '0.9rem' }
            }}
          />

          {/* Execute Button */}
          <Button
            fullWidth
            variant="contained"
            size="large"
            onClick={handleExecute}
            disabled={!dockerAvailable || isExecuting || !testCode.trim()}
            startIcon={isExecuting ? <CircularProgress size={20} /> : <PlayIcon />}
          >
            {isExecuting ? 'Executing in Docker...' : 'Execute in Docker Container'}
          </Button>

          {/* Error Display */}
          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}

          {/* Execution Results */}
          {executionResult && (
            <Box sx={{ mt: 3 }}>
              <Divider sx={{ mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Execution Results
              </Typography>
              
              <Alert 
                severity={executionResult.success ? "success" : "error"}
                sx={{ mb: 2 }}
              >
                {executionResult.success ? 'Execution Completed Successfully' : 'Execution Failed'}
                {executionResult.exit_code !== undefined && (
                  <Typography variant="body2">
                    Exit Code: {executionResult.exit_code}
                  </Typography>
                )}
              </Alert>

              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>
                    Output:
                  </Typography>
                  <Box
                    component="pre"
                    sx={{
                      p: 2,
                      bgcolor: 'grey.100',
                      borderRadius: 1,
                      overflow: 'auto',
                      maxHeight: 400,
                      fontFamily: 'Courier New, monospace',
                      fontSize: '0.85rem',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word'
                    }}
                  >
                    {executionResult.output || 'No output'}
                  </Box>
                  
                  {executionResult.error && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle2" color="error" gutterBottom>
                        Error:
                      </Typography>
                      <Typography
                        variant="body2"
                        color="error"
                        sx={{ fontFamily: 'monospace' }}
                      >
                        {executionResult.error}
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Docker Info */}
      {dockerAvailable && (
        <Card sx={{ mt: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Docker Environment Info
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">Available Images:</Typography>
                <Box sx={{ mt: 1 }}>
                  {dockerImages.slice(0, 5).map((image, idx) => (
                    <Chip
                      key={idx}
                      label={image}
                      size="small"
                      sx={{ mr: 1, mb: 1 }}
                    />
                  ))}
                  {dockerImages.length > 5 && (
                    <Chip
                      label={`+${dockerImages.length - 5} more`}
                      size="small"
                      variant="outlined"
                    />
                  )}
                </Box>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">Container Status:</Typography>
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Total Containers: {containerStatus.total_containers || 0}
                </Typography>
                <Typography variant="body2">
                  STLC Containers: {containerStatus.stlc_containers?.length || 0}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default DockerExecutionPanel;
