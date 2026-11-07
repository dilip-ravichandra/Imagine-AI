import React from 'react';
import { Box, Flex, Grid, GridItem, Text, Heading, Stat, StatLabel, StatNumber, StatHelpText } from '@chakra-ui/react';
import WorkspaceLayout from '../components/WorkspaceLayout';

const statCards = [
  { label: 'Total Users', value: '1,248', change: '+12%', icon: '👥' },
  { label: 'Total Generations', value: '56,320', change: '+8%', icon: '🖼️' },
  { label: 'Active Sessions', value: '312', change: '+5%', icon: '📊' },
  { label: 'Uptime', value: '99.9%', change: 'Stable', icon: '✅' },
];

const recentActivity = [
  { user: 'dilip@email.com', action: 'Generated 3 images', time: '2 min ago', status: 'success' },
  { user: 'sarah@email.com', action: 'Started training job', time: '15 min ago', status: 'active' },
  { user: 'mike@email.com', action: 'Uploaded dataset', time: '1 hour ago', status: 'success' },
  { user: 'anna@email.com', action: 'Reported issue', time: '2 hours ago', status: 'warning' },
  { user: 'john@email.com', action: 'Signed up', time: '3 hours ago', status: 'success' },
];

const quickActions = [
  { label: 'User Management', icon: '👥', desc: 'Manage users and roles' },
  { label: 'Model Registry', icon: '🤖', desc: 'Deploy and manage models' },
  { label: 'System Health', icon: '💚', desc: 'Monitor services' },
  { label: 'Service Control', icon: '⚙️', desc: 'Feature flags and config' },
];

const AdminDashboard: React.FC = () => {
  return (
    <WorkspaceLayout>
      <Box p={8} maxW="1400px">
        {/* Header */}
        <Flex justify="space-between" align="center" mb={8}>
          <Box>
            <Heading size="lg" color="#F4F7F0" fontWeight="700">
              Admin Dashboard
            </Heading>
            <Text color="#A5B1A7" fontSize="14px" mt={1}>
              System overview and management
            </Text>
          </Box>
          <Flex gap={2}>
            <Text fontSize="12px" color="#6B7B6D" bg="#111713" px={3} py={1.5} borderRadius="8px" border="1px solid #2A3A2C">
              Last 7 Days
            </Text>
          </Flex>
        </Flex>

        {/* Stats Cards */}
        <Grid templateColumns="repeat(4, 1fr)" gap={5} mb={8}>
          {statCards.map((stat, i) => (
            <GridItem key={i}>
              <Box
                bg="#111713"
                border="1px solid #2A3A2C"
                borderRadius="14px"
                p={5}
                _hover={{ borderColor: '#3A4A3C' }}
                transition="all 0.2s ease"
              >
                <Flex justify="space-between" align="flex-start" mb={3}>
                  <Text fontSize="13px" color="#A5B1A7" fontWeight="500">{stat.label}</Text>
                  <Text fontSize="20px">{stat.icon}</Text>
                </Flex>
                <Text fontSize="28px" fontWeight="700" color="#F4F7F0" mb={1}>
                  {stat.value}
                </Text>
                <Text fontSize="12px" color="#B7FF35" fontWeight="500">
                  {stat.change}
                </Text>
              </Box>
            </GridItem>
          ))}
        </Grid>

        <Grid templateColumns="2fr 1fr" gap={6}>
          {/* Recent Activity */}
          <GridItem>
            <Box
              bg="#111713"
              border="1px solid #2A3A2C"
              borderRadius="14px"
              overflow="hidden"
            >
              <Flex
                px={5}
                py={4}
                borderBottom="1px solid #2A3A2C"
                align="center"
                justify="space-between"
              >
                <Text fontWeight="600" color="#F4F7F0" fontSize="15px">Recent Activity</Text>
                <Text fontSize="12px" color="#B7FF35" cursor="pointer" _hover={{ textDecoration: 'underline' }}>
                  View All
                </Text>
              </Flex>
              {recentActivity.map((item, i) => (
                <Flex
                  key={i}
                  px={5}
                  py={3.5}
                  align="center"
                  justify="space-between"
                  borderBottom={i < recentActivity.length - 1 ? '1px solid #1A2A1C' : 'none'}
                  _hover={{ bg: '#0D120E' }}
                  transition="bg 0.15s ease"
                >
                  <Flex align="center" gap={3}>
                    <Box
                      w="32px"
                      h="32px"
                      borderRadius="full"
                      bg="#182019"
                      display="flex"
                      alignItems="center"
                      justifyContent="center"
                      fontSize="12px"
                      color="#A5B1A7"
                      fontWeight="600"
                    >
                      {item.user.charAt(0).toUpperCase()}
                    </Box>
                    <Box>
                      <Text fontSize="13px" color="#F4F7F0" fontWeight="500">{item.action}</Text>
                      <Text fontSize="11px" color="#6B7B6D">{item.user}</Text>
                    </Box>
                  </Flex>
                  <Flex align="center" gap={3}>
                    <Box
                      w="8px"
                      h="8px"
                      borderRadius="full"
                      bg={item.status === 'success' ? '#B7FF35' : item.status === 'active' ? '#4FC3F7' : '#FFB800'}
                    />
                    <Text fontSize="11px" color="#6B7B6D">{item.time}</Text>
                  </Flex>
                </Flex>
              ))}
            </Box>
          </GridItem>

          {/* Quick Actions */}
          <GridItem>
            <Box
              bg="#111713"
              border="1px solid #2A3A2C"
              borderRadius="14px"
              overflow="hidden"
            >
              <Box px={5} py={4} borderBottom="1px solid #2A3A2C">
                <Text fontWeight="600" color="#F4F7F0" fontSize="15px">Quick Actions</Text>
              </Box>
              {quickActions.map((action, i) => (
                <Flex
                  key={i}
                  px={5}
                  py={4}
                  align="center"
                  gap={3}
                  cursor="pointer"
                  borderBottom={i < quickActions.length - 1 ? '1px solid #1A2A1C' : 'none'}
                  _hover={{ bg: '#182019' }}
                  transition="all 0.15s ease"
                >
                  <Box
                    w="36px"
                    h="36px"
                    borderRadius="10px"
                    bg="#182019"
                    display="flex"
                    alignItems="center"
                    justifyContent="center"
                    fontSize="18px"
                    border="1px solid #2A3A2C"
                  >
                    {action.icon}
                  </Box>
                  <Box>
                    <Text fontSize="13px" color="#F4F7F0" fontWeight="500">{action.label}</Text>
                    <Text fontSize="11px" color="#6B7B6D">{action.desc}</Text>
                  </Box>
                </Flex>
              ))}
            </Box>

            {/* System Status */}
            <Box
              bg="#111713"
              border="1px solid #2A3A2C"
              borderRadius="14px"
              p={5}
              mt={5}
            >
              <Text fontWeight="600" color="#F4F7F0" fontSize="15px" mb={4}>System Status</Text>
              {[
                { name: 'API Server', status: 'Operational', color: '#B7FF35' },
                { name: 'GPU Cluster', status: 'Operational', color: '#B7FF35' },
                { name: 'Database', status: 'Operational', color: '#B7FF35' },
                { name: 'CDN', status: 'Degraded', color: '#FFB800' },
              ].map((svc, i) => (
                <Flex key={i} justify="space-between" align="center" mb={i < 3 ? 3 : 0}>
                  <Text fontSize="13px" color="#A5B1A7">{svc.name}</Text>
                  <Flex align="center" gap={2}>
                    <Box w="6px" h="6px" borderRadius="full" bg={svc.color} />
                    <Text fontSize="11px" color={svc.color}>{svc.status}</Text>
                  </Flex>
                </Flex>
              ))}
            </Box>
          </GridItem>
        </Grid>
      </Box>
    </WorkspaceLayout>
  );
};

export default AdminDashboard;
