import React, { useState } from 'react';
import {
  Box,
  Flex,
  Text,
  Heading,
  Button,
  Input,
  Image,
  VStack,
  HStack,
  IconButton,
  Avatar,
} from '@chakra-ui/react';
import {
  FiUpload,
  FiSend,
  FiImage,
  FiMessageCircle,
  FiCopy,
  FiThumbsUp,
  FiRefreshCw,
  FiZoomIn,
} from 'react-icons/fi';
import WorkspaceLayout from '../components/WorkspaceLayout';

interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  text: string;
  timestamp: string;
}

const AskYourImage: React.FC = () => {
  const [inputValue, setInputValue] = useState('');
  const [hasImage, setHasImage] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 1,
      role: 'user',
      text: 'What is this insect? Explain simply.',
      timestamp: '2:34 PM',
    },
    {
      id: 2,
      role: 'assistant',
      text: 'This is a butterfly. Butterflies are insects with colorful wings. They help plants grow by spreading pollen from one flower to another. This particular one appears to be a Monarch butterfly, identifiable by its orange and black wing pattern. Monarchs are famous for their long migration journeys across continents.',
      timestamp: '2:34 PM',
    },
    {
      id: 3,
      role: 'user',
      text: 'What colors can you see in its wings?',
      timestamp: '2:35 PM',
    },
    {
      id: 4,
      role: 'assistant',
      text: 'The butterfly\'s wings display a striking combination of colors:\n\n• **Deep orange** — the primary color covering most of the wing surface\n• **Black** — bold veins and borders creating the distinctive pattern\n• **White** — small spots along the wing edges\n• **Yellow-gold** — subtle highlights near the wing bases\n\nThis vivid coloring serves as a warning to predators that the butterfly is toxic, a defense mechanism known as aposematism.',
      timestamp: '2:35 PM',
    },
    {
      id: 5,
      role: 'user',
      text: 'Is it endangered?',
      timestamp: '2:36 PM',
    },
    {
      id: 6,
      role: 'assistant',
      text: 'The Monarch butterfly is currently classified as **endangered** by the IUCN. Their population has declined significantly due to habitat loss, pesticide use, and climate change. Conservation efforts are underway globally, including planting milkweed (their primary food source) and protecting migration corridors.',
      timestamp: '2:36 PM',
    },
  ]);

  const handleSend = () => {
    if (!inputValue.trim()) return;
    const newMsg: ChatMessage = {
      id: messages.length + 1,
      role: 'user',
      text: inputValue,
      timestamp: new Date().toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      }),
    };
    setMessages([...messages, newMsg]);
    setInputValue('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <WorkspaceLayout>
      <Box p={6} minH="100vh" bg="#080B0A">
        {/* Header */}
        <Flex align="center" justify="space-between" mb={6}>
          <Box>
            <Flex align="center" gap={3} mb={1}>
              <Box
                p={2}
                bg="rgba(183, 255, 53, 0.1)"
                borderRadius="lg"
              >
                <FiMessageCircle size={20} color="#B7FF35" />
              </Box>
              <Box>
                <Heading size="lg" color="#F4F7F0" fontWeight="700">
                  Ask Your Image
                </Heading>
                <Text color="#A5B1A7" fontSize="sm">
                  Upload an image and ask anything about it
                </Text>
              </Box>
            </Flex>
          </Box>
          <HStack spacing={2}>
            <Button
              size="sm"
              variant="outline"
              borderColor="#2A3A2C"
              color="#A5B1A7"
              _hover={{ bg: '#1A2A1C', borderColor: '#B7FF35', color: '#F4F7F0' }}
              leftIcon={<FiRefreshCw size={14} />}
              fontSize="xs"
            >
              New Session
            </Button>
          </HStack>
        </Flex>

        {/* Main Layout */}
        <Flex gap={6} h="calc(100vh - 160px)">
          {/* Left: Image Area */}
          <Box
            w="420px"
            minW="420px"
            display="flex"
            flexDir="column"
            gap={4}
          >
            {/* Upload Zone */}
            {!hasImage ? (
              <Box
                flex={1}
                bg="#111713"
                border="2px dashed #2A3A2C"
                borderRadius="xl"
                display="flex"
                flexDir="column"
                alignItems="center"
                justifyContent="center"
                cursor="pointer"
                _hover={{ borderColor: '#B7FF35', bg: '#182019' }}
                transition="all 0.2s"
                onClick={() => setHasImage(true)}
              >
                <Box
                  p={4}
                  bg="rgba(183,255,53,0.05)"
                  borderRadius="full"
                  mb={4}
                >
                  <FiUpload size={32} color="#B7FF35" />
                </Box>
                <Text color="#F4F7F0" fontSize="md" fontWeight="600" mb={1}>
                  Drop your image here
                </Text>
                <Text color="#A5B1A7" fontSize="sm" mb={4}>
                  or click to browse files
                </Text>
                <HStack spacing={2}>
                  <Text
                    bg="#0F1A11"
                    px={3}
                    py={1}
                    borderRadius="full"
                    color="#A5B1A7"
                    fontSize="xs"
                  >
                    PNG
                  </Text>
                  <Text
                    bg="#0F1A11"
                    px={3}
                    py={1}
                    borderRadius="full"
                    color="#A5B1A7"
                    fontSize="xs"
                  >
                    JPG
                  </Text>
                  <Text
                    bg="#0F1A11"
                    px={3}
                    py={1}
                    borderRadius="full"
                    color="#A5B1A7"
                    fontSize="xs"
                  >
                    WEBP
                  </Text>
                  <Text
                    bg="#0F1A11"
                    px={3}
                    py={1}
                    borderRadius="full"
                    color="#A5B1A7"
                    fontSize="xs"
                  >
                    up to 20MB
                  </Text>
                </HStack>
              </Box>
            ) : (
              <Box
                flex={1}
                bg="#111713"
                borderRadius="xl"
                border="1px solid #2A3A2C"
                overflow="hidden"
                display="flex"
                flexDir="column"
              >
                {/* Image Display */}
                <Box flex={1} position="relative" overflow="hidden">
                  <Image
                    src="https://picsum.photos/seed/butterfly-nature/800/800"
                    alt="Uploaded butterfly image"
                    w="100%"
                    h="100%"
                    objectFit="cover"
                  />
                  {/* Overlay controls */}
                  <Flex
                    position="absolute"
                    top={3}
                    right={3}
                    gap={2}
                  >
                    <IconButton
                      aria-label="Zoom in"
                      icon={<FiZoomIn size={14} />}
                      size="sm"
                      bg="rgba(8,11,10,0.7)"
                      color="#F4F7F0"
                      borderRadius="lg"
                      backdropFilter="blur(10px)"
                      _hover={{ bg: 'rgba(8,11,10,0.9)' }}
                    />
                  </Flex>
                  {/* Image info bar */}
                  <Flex
                    position="absolute"
                    bottom={0}
                    left={0}
                    right={0}
                    bg="linear-gradient(transparent, rgba(8,11,10,0.9))"
                    px={4}
                    py={3}
                    align="center"
                    justify="space-between"
                  >
                    <HStack spacing={3}>
                      <Text color="#A5B1A7" fontSize="xs">
                        butterfly_monarch.jpg
                      </Text>
                      <Text color="#2A3A2C">•</Text>
                      <Text color="#A5B1A7" fontSize="xs">
                        2400 × 2400
                      </Text>
                    </HStack>
                    <Button
                      size="xs"
                      variant="ghost"
                      color="#B7FF35"
                      _hover={{ bg: 'rgba(183,255,53,0.1)' }}
                      fontSize="xs"
                      onClick={() => setHasImage(false)}
                    >
                      Change
                    </Button>
                  </Flex>
                </Box>

                {/* Quick suggestions */}
                <Box px={4} py={3} borderTop="1px solid #2A3A2C">
                  <Text color="#A5B1A7" fontSize="10px" fontWeight="600" mb={2} textTransform="uppercase" letterSpacing="wider">
                    Suggested Questions
                  </Text>
                  <Flex gap={2} flexWrap="wrap">
                    {[
                      'Describe this image',
                      'What species is this?',
                      'Extract text',
                      'Identify objects',
                    ].map((q) => (
                      <Box
                        key={q}
                        px={3}
                        py={1.5}
                        bg="#0F1A11"
                        border="1px solid #2A3A2C"
                        borderRadius="full"
                        cursor="pointer"
                        _hover={{
                          borderColor: '#B7FF35',
                          bg: '#1A2A1C',
                        }}
                        transition="all 0.2s"
                        onClick={() => setInputValue(q)}
                      >
                        <Text color="#A5B1A7" fontSize="xs" _hover={{ color: '#F4F7F0' }}>
                          {q}
                        </Text>
                      </Box>
                    ))}
                  </Flex>
                </Box>
              </Box>
            )}
          </Box>

          {/* Right: Chat Interface */}
          <Box
            flex={1}
            bg="#111713"
            borderRadius="xl"
            border="1px solid #2A3A2C"
            display="flex"
            flexDir="column"
            overflow="hidden"
          >
            {/* Chat Header */}
            <Flex
              align="center"
              justify="space-between"
              px={5}
              py={3}
              borderBottom="1px solid #2A3A2C"
            >
              <Flex align="center" gap={2}>
                <Box
                  w={2}
                  h={2}
                  bg="#B7FF35"
                  borderRadius="full"
                  boxShadow="0 0 6px #B7FF35"
                />
                <Text color="#F4F7F0" fontSize="sm" fontWeight="600">
                  Visual Q&A
                </Text>
              </Flex>
              <Text color="#A5B1A7" fontSize="xs">
                {messages.length} messages
              </Text>
            </Flex>

            {/* Messages Area */}
            <Box
              flex={1}
              overflowY="auto"
              px={5}
              py={4}
              css={{
                '&::-webkit-scrollbar': { width: '4px' },
                '&::-webkit-scrollbar-track': { bg: 'transparent' },
                '&::-webkit-scrollbar-thumb': {
                  bg: '#2A3A2C',
                  borderRadius: '4px',
                },
              }}
            >
              <VStack spacing={4} align="stretch">
                {messages.map((msg) => (
                  <Flex
                    key={msg.id}
                    justify={msg.role === 'user' ? 'flex-end' : 'flex-start'}
                    gap={3}
                  >
                    {msg.role === 'assistant' && (
                      <Box
                        w={8}
                        h={8}
                        bg="rgba(183,255,53,0.1)"
                        borderRadius="lg"
                        display="flex"
                        alignItems="center"
                        justifyContent="center"
                        flexShrink={0}
                        mt={1}
                      >
                        <Text fontSize="sm">🤖</Text>
                      </Box>
                    )}
                    <Box maxW="75%">
                      <Box
                        bg={msg.role === 'user' ? '#B7FF35' : '#182019'}
                        color={msg.role === 'user' ? '#080B0A' : '#F4F7F0'}
                        px={4}
                        py={3}
                        borderRadius={
                          msg.role === 'user'
                            ? '18px 18px 4px 18px'
                            : '18px 18px 18px 4px'
                        }
                        border={
                          msg.role === 'assistant'
                            ? '1px solid #2A3A2C'
                            : 'none'
                        }
                      >
                        <Text
                          fontSize="sm"
                          lineHeight="1.7"
                          fontWeight={msg.role === 'user' ? '600' : '400'}
                          whiteSpace="pre-wrap"
                        >
                          {msg.text}
                        </Text>
                      </Box>
                      <Flex
                        mt={1.5}
                        align="center"
                        gap={2}
                        justify={
                          msg.role === 'user' ? 'flex-end' : 'flex-start'
                        }
                      >
                        <Text color="#A5B1A7" fontSize="10px">
                          {msg.timestamp}
                        </Text>
                        {msg.role === 'assistant' && (
                          <HStack spacing={1}>
                            <IconButton
                              aria-label="Copy"
                              icon={<FiCopy size={10} />}
                              size="xs"
                              variant="ghost"
                              color="#A5B1A7"
                              _hover={{ color: '#B7FF35' }}
                              minW="auto"
                              h="auto"
                              p={1}
                            />
                            <IconButton
                              aria-label="Like"
                              icon={<FiThumbsUp size={10} />}
                              size="xs"
                              variant="ghost"
                              color="#A5B1A7"
                              _hover={{ color: '#B7FF35' }}
                              minW="auto"
                              h="auto"
                              p={1}
                            />
                          </HStack>
                        )}
                      </Flex>
                    </Box>
                    {msg.role === 'user' && (
                      <Avatar
                        size="sm"
                        name="User"
                        bg="#2A3A2C"
                        color="#F4F7F0"
                        mt={1}
                      />
                    )}
                  </Flex>
                ))}
              </VStack>
            </Box>

            {/* Input Area */}
            <Box px={5} py={4} borderTop="1px solid #2A3A2C">
              <Flex
                bg="#0F1A11"
                border="1px solid #2A3A2C"
                borderRadius="xl"
                px={4}
                py={2}
                align="center"
                gap={3}
                _focusWithin={{
                  borderColor: '#B7FF35',
                  boxShadow: '0 0 0 1px rgba(183,255,53,0.2)',
                }}
                transition="all 0.2s"
              >
                <Input
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask a question about the image..."
                  variant="unstyled"
                  color="#F4F7F0"
                  fontSize="sm"
                  _placeholder={{ color: '#A5B1A7' }}
                  flex={1}
                />
                <IconButton
                  aria-label="Send message"
                  icon={<FiSend size={16} />}
                  size="sm"
                  bg={inputValue.trim() ? '#B7FF35' : '#2A3A2C'}
                  color={inputValue.trim() ? '#080B0A' : '#A5B1A7'}
                  borderRadius="lg"
                  _hover={{
                    bg: inputValue.trim() ? '#8DDB39' : '#2A3A2C',
                    transform: inputValue.trim()
                      ? 'translateY(-1px)'
                      : 'none',
                  }}
                  transition="all 0.2s"
                  onClick={handleSend}
                  isDisabled={!inputValue.trim()}
                />
              </Flex>
              <Text color="#A5B1A7" fontSize="10px" mt={2} textAlign="center">
                AI-powered visual analysis • Responses may not be 100% accurate
              </Text>
            </Box>
          </Box>
        </Flex>
      </Box>
    </WorkspaceLayout>
  );
};

export default AskYourImage;
