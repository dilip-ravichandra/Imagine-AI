import React, { useState } from 'react';
import { Box, Flex, Text, VStack, Icon } from '@chakra-ui/react';
import { Link, useLocation } from 'react-router-dom';

const NAV_ITEMS = [
  { label: 'Home', path: '/dashboard', icon: '🏠' },
  { label: 'Create', path: '/create', icon: '🎨' },
  { label: 'Learn', path: '/learn', icon: '📚' },
  { label: 'Edit', path: '/edit', icon: '✏️' },
  { label: 'Canvas', path: '/canvas', icon: '🖼️' },
  { label: 'Storybook', path: '/storybook', icon: '📖' },
  { label: 'Gallery', path: '/gallery', icon: '🖼️' },
  { label: 'Ask Image', path: '/ask-image', icon: '🔍' },
  { label: 'Voice', path: '/voice', icon: '🎤' },
];

const ADMIN_ITEMS = [
  { label: 'Profile', path: '/profile', icon: '👤' },
  { label: 'Research', path: '/research', icon: '📊' },
  { label: 'Training', path: '/training', icon: '🧪' },
  { label: 'Admin', path: '/admin', icon: '⚙️' },
];

const Sidebar: React.FC = () => {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <Box
      as="nav"
      w={collapsed ? '70px' : '220px'}
      minH="100vh"
      bg="#0D120E"
      borderRight="1px solid #2A3A2C"
      py={4}
      transition="width 0.2s ease"
      position="fixed"
      left={0}
      top={0}
      zIndex={100}
      display="flex"
      flexDirection="column"
    >
      {/* Logo */}
      <Flex
        align="center"
        px={collapsed ? 3 : 5}
        py={3}
        mb={4}
        cursor="pointer"
        onClick={() => setCollapsed(!collapsed)}
      >
        <Box
          w="32px"
          h="32px"
          borderRadius="8px"
          bg="#B7FF35"
          display="flex"
          alignItems="center"
          justifyContent="center"
          fontSize="18px"
          fontWeight="bold"
          color="#080B0A"
          flexShrink={0}
        >
          I
        </Box>
        {!collapsed && (
          <Text ml={3} fontSize="lg" fontWeight="bold" color="#F4F7F0" letterSpacing="-0.5px">
            ImagineAI
          </Text>
        )}
      </Flex>

      {/* Main Nav */}
      <VStack spacing={1} align="stretch" flex={1} px={2}>
        {NAV_ITEMS.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link key={item.path} to={item.path}>
              <Flex
                align="center"
                px={collapsed ? 3 : 4}
                py={2.5}
                borderRadius="10px"
                bg={isActive ? '#1A2A1C' : 'transparent'}
                color={isActive ? '#B7FF35' : '#A5B1A7'}
                _hover={{ bg: '#1A2A1C', color: '#F4F7F0' }}
                transition="all 0.15s ease"
                cursor="pointer"
                justify={collapsed ? 'center' : 'flex-start'}
              >
                <Text fontSize="18px" lineHeight="1">{item.icon}</Text>
                {!collapsed && (
                  <Text ml={3} fontSize="14px" fontWeight={isActive ? '600' : '400'}>
                    {item.label}
                  </Text>
                )}
              </Flex>
            </Link>
          );
        })}

        <Box h="1px" bg="#2A3A2C" my={3} mx={2} />

        {ADMIN_ITEMS.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link key={item.path} to={item.path}>
              <Flex
                align="center"
                px={collapsed ? 3 : 4}
                py={2.5}
                borderRadius="10px"
                bg={isActive ? '#1A2A1C' : 'transparent'}
                color={isActive ? '#B7FF35' : '#6B7B6D'}
                _hover={{ bg: '#1A2A1C', color: '#A5B1A7' }}
                transition="all 0.15s ease"
                cursor="pointer"
                fontSize="13px"
                justify={collapsed ? 'center' : 'flex-start'}
              >
                <Text fontSize="16px" lineHeight="1">{item.icon}</Text>
                {!collapsed && (
                  <Text ml={3} fontSize="13px" fontWeight={isActive ? '600' : '400'}>
                    {item.label}
                  </Text>
                )}
              </Flex>
            </Link>
          );
        })}
      </VStack>

      {/* User Footer Profile */}
      <Box p={2} borderTop="1px solid #2A3A2C" mt="auto">
        <Link to="/profile">
          <Flex
            align="center"
            p={2}
            borderRadius="10px"
            _hover={{ bg: '#182019' }}
            cursor="pointer"
            justify={collapsed ? 'center' : 'flex-start'}
          >
            <Box
              w="32px"
              h="32px"
              borderRadius="full"
              bg="#182019"
              border="1px solid #B7FF35"
              display="flex"
              alignItems="center"
              justifyContent="center"
              fontSize="12px"
              fontWeight="bold"
              color="#B7FF35"
              flexShrink={0}
            >
              D
            </Box>
            {!collapsed && (
              <Box ml={3} overflow="hidden">
                <Flex align="center" gap={1.5}>
                  <Text fontSize="13px" fontWeight="600" color="#F4F7F0" isTruncated>
                    Dilip R.
                  </Text>
                  <Box bg="rgba(183, 255, 53, 0.2)" color="#B7FF35" fontSize="10px" px={1.5} py={0.2} borderRadius="4px" fontWeight="bold">
                    PRO
                  </Box>
                </Flex>
                <Text fontSize="11px" color="#6B7B6D" isTruncated>
                  dilip@example.com
                </Text>
              </Box>
            )}
          </Flex>
        </Link>
      </Box>
    </Box>
  );
};

export default Sidebar;
