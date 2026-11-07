import React from 'react';
import { Box, Flex } from '@chakra-ui/react';
import Sidebar from './Sidebar';
import ChatBot from './ChatBot';

interface WorkspaceLayoutProps {
  children: React.ReactNode;
}

const WorkspaceLayout: React.FC<WorkspaceLayoutProps> = ({ children }) => {
  return (
    <Flex minH="100vh" bg="#080B0A">
      <Sidebar />
      <Box
        flex={1}
        ml="220px"
        minH="100vh"
        transition="margin-left 0.2s ease"
      >
        {children}
      </Box>
      <ChatBot />
    </Flex>
  );
};

export default WorkspaceLayout;
