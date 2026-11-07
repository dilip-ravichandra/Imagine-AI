import React, { useState } from 'react';
import { Box, Flex, Input, InputGroup, InputLeftElement, InputRightElement, Text, IconButton } from '@chakra-ui/react';

interface ChatBotProps {
  isOpen?: boolean;
}

const ChatBot: React.FC<ChatBotProps> = ({ isOpen: initialOpen = false }) => {
  const [isOpen, setIsOpen] = useState(initialOpen);
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant'; text: string }[]>([
    { role: 'assistant', text: 'Hi! I\'m the Imagine AI Assistant powered by Groq. How can I help you today? I can assist with creating images, learning topics, editing, and more.' },
  ]);

  const sendMessage = () => {
    if (!message.trim()) return;
    setMessages((prev) => [...prev, { role: 'user', text: message }]);
    // Simulate assistant response
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `Great question! I can help you with that. Let me think about "${message.slice(0, 50)}..." — try navigating to the Create Studio or Learn Studio for the best experience.`,
        },
      ]);
    }, 800);
    setMessage('');
  };

  const handleLauncherSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) {
      setIsOpen(true);
      return;
    }
    setIsOpen(true);
    sendMessage();
  };

  return (
    <>
      {/* Floating Launcher Bar */}
      {!isOpen && (
        <Box
          position="fixed"
          bottom="20px"
          left="50%"
          transform="translateX(-50%)"
          zIndex={1000}
          w="calc(100% - 40px)"
          maxW="860px"
        >
          <Box
            as="form"
            onSubmit={handleLauncherSubmit}
            bg="#0D120E"
            border="1px solid #3A4A3C"
            borderRadius="full"
            px={5}
            py={2.5}
            boxShadow="0 10px 40px rgba(0,0,0,0.7), 0 0 25px rgba(183,255,53,0.15)"
            _hover={{ borderColor: '#B7FF35' }}
            transition="all 0.25s ease"
          >
            <Flex align="center" gap={3}>
              {/* Green Logo Icon */}
              <Flex
                align="center"
                gap={2}
                cursor="pointer"
                onClick={() => setIsOpen(true)}
                flexShrink={0}
              >
                <Box
                  w="34px"
                  h="34px"
                  borderRadius="full"
                  bg="#B7FF35"
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                  fontSize="16px"
                  fontWeight="bold"
                  color="#080B0A"
                  boxShadow="0 0 12px rgba(183,255,53,0.4)"
                >
                  ✦
                </Box>
                <Box display={{ base: 'none', md: 'block' }}>
                  <Text fontSize="13px" fontWeight="700" color="#F4F7F0" lineHeight="1.2">
                    Imagine Assistant
                  </Text>
                  <Text fontSize="10px" color="#8DDB39" fontWeight="600">
                    Powered by Groq
                  </Text>
                </Box>
              </Flex>

              <Box w="1px" h="24px" bg="#2A3A2C" mx={1} display={{ base: 'none', md: 'block' }} />

              {/* Direct interactive input */}
              <Input
                placeholder="Ask me anything about creating, learning, editing, or using ImagineAI..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                variant="unstyled"
                color="#F4F7F0"
                fontSize="14px"
                _placeholder={{ color: '#6B7B6D' }}
                flex={1}
                px={2}
              />

              {/* Voice icon */}
              <IconButton
                aria-label="Voice input"
                icon={<Text fontSize="16px">🎤</Text>}
                size="sm"
                variant="ghost"
                color="#A5B1A7"
                _hover={{ color: '#B7FF35', bg: '#182019' }}
                borderRadius="full"
                onClick={() => setIsOpen(true)}
              />

              {/* Send button */}
              <IconButton
                aria-label="Send message"
                type="submit"
                icon={<Text fontSize="14px" fontWeight="bold">➤</Text>}
                size="sm"
                bg="#B7FF35"
                color="#080B0A"
                borderRadius="full"
                _hover={{ bg: '#8DDB39', transform: 'scale(1.05)' }}
                transition="all 0.2s"
              />
            </Flex>
          </Box>
        </Box>
      )}

      {/* Chat Panel */}
      {isOpen && (
        <Box
          position="fixed"
          bottom="24px"
          right="24px"
          w="420px"
          h="500px"
          bg="#111713"
          border="1px solid #2A3A2C"
          borderRadius="16px"
          zIndex={1001}
          display="flex"
          flexDirection="column"
          boxShadow="0 16px 64px rgba(0,0,0,0.6)"
          overflow="hidden"
        >
          {/* Header */}
          <Flex
            bg="#0D120E"
            px={4}
            py={3}
            align="center"
            justify="space-between"
            borderBottom="1px solid #2A3A2C"
          >
            <Flex align="center" gap={2}>
              <Box w="24px" h="24px" borderRadius="full" bg="#B7FF35" display="flex" alignItems="center" justifyContent="center" fontSize="12px" fontWeight="bold" color="#080B0A">
                ✦
              </Box>
              <Text fontWeight="600" color="#F4F7F0" fontSize="14px">Imagine Assistant</Text>
              <Text fontSize="10px" color="#6B7B6D" bg="#182019" px={2} py={0.5} borderRadius="full">Groq</Text>
            </Flex>
            <Text
              cursor="pointer"
              onClick={() => setIsOpen(false)}
              color="#6B7B6D"
              _hover={{ color: '#F4F7F0' }}
              fontSize="18px"
            >
              ✕
            </Text>
          </Flex>

          {/* Messages */}
          <Box flex={1} overflowY="auto" p={4}>
            {messages.map((msg, i) => (
              <Flex key={i} justify={msg.role === 'user' ? 'flex-end' : 'flex-start'} mb={3}>
                <Box
                  maxW="85%"
                  px={4}
                  py={2.5}
                  borderRadius={msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px'}
                  bg={msg.role === 'user' ? '#B7FF35' : '#182019'}
                  color={msg.role === 'user' ? '#080B0A' : '#F4F7F0'}
                  fontSize="13px"
                  lineHeight="1.5"
                >
                  {msg.text}
                </Box>
              </Flex>
            ))}
          </Box>

          {/* Input */}
          <Flex p={3} borderTop="1px solid #2A3A2C" gap={2}>
            <Input
              placeholder="Ask me anything..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              bg="#0F1A11"
              border="1px solid #2A3A2C"
              borderRadius="12px"
              color="#F4F7F0"
              _placeholder={{ color: '#6B7B6D' }}
              _focus={{ borderColor: '#B7FF35' }}
              size="sm"
            />
            <Box
              as="button"
              w="36px"
              h="36px"
              borderRadius="10px"
              bg="#B7FF35"
              display="flex"
              alignItems="center"
              justifyContent="center"
              fontSize="14px"
              color="#080B0A"
              cursor="pointer"
              flexShrink={0}
              onClick={sendMessage}
              _hover={{ bg: '#8DDB39' }}
            >
              ➤
            </Box>
          </Flex>
        </Box>
      )}
    </>
  );
};

export default ChatBot;
