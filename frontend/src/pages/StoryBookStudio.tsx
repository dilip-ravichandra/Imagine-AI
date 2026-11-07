import React, { useState } from 'react';
import {
  Box,
  Flex,
  Text,
  Heading,
  Button,
  Input,
  Textarea,
  Select,
  Image,
  VStack,
  HStack,
  IconButton,
  Divider,
  Badge,
} from '@chakra-ui/react';
import {
  FiChevronLeft,
  FiChevronRight,
  FiBookOpen,
  FiEdit3,
  FiDownload,
  FiShare2,
  FiStar,
} from 'react-icons/fi';
import WorkspaceLayout from '../components/WorkspaceLayout';

interface StoryPage {
  id: number;
  image: string;
  text: string;
}

const StoryBookStudio: React.FC = () => {
  const [storyTitle, setStoryTitle] = useState('The Little Robot and His New Friend');
  const [storyIdea, setStoryIdea] = useState(
    'A little robot who lives in a futuristic city discovers a stray kitten. Together they learn about friendship, kindness, and what it means to care for someone.'
  );
  const [style, setStyle] = useState('children');
  const [pageCount, setPageCount] = useState(6);
  const [currentPage, setCurrentPage] = useState(0);

  const storyPages: StoryPage[] = [
    {
      id: 1,
      image: 'https://picsum.photos/seed/story-robot1/600/400',
      text: 'In a shimmering city of glass and light, there lived a little robot named Bolt. Every morning, Bolt would wake up, polish his silver arms, and roll out to explore the world.',
    },
    {
      id: 2,
      image: 'https://picsum.photos/seed/story-kitten2/600/400',
      text: 'One rainy afternoon, Bolt heard a tiny sound coming from behind a recycling bin. "Meow!" It was a small orange kitten, shivering and alone. Bolt had never seen anything so soft.',
    },
    {
      id: 3,
      image: 'https://picsum.photos/seed/story-friends3/600/400',
      text: '"Don\'t worry," said Bolt, carefully scooping the kitten into his metal arms. "I\'ll keep you warm." The kitten purred, and for the first time, Bolt felt something glow inside his circuits.',
    },
    {
      id: 4,
      image: 'https://picsum.photos/seed/story-play4/600/400',
      text: 'Bolt named the kitten Spark. Together they explored the city — Spark chasing butterflies while Bolt rolled alongside, his eyes flashing with joy.',
    },
    {
      id: 5,
      image: 'https://picsum.photos/seed/story-learn5/600/400',
      text: 'Spark taught Bolt that friendship isn\'t about being the same. It\'s about caring for each other, even when you\'re made of different things — fur and metal, whiskers and wires.',
    },
    {
      id: 6,
      image: 'https://picsum.photos/seed/story-end6/600/400',
      text: 'And every night, as the city lights painted the sky, Bolt and Spark would sit on the rooftop together — a robot and his best friend — watching the stars come alive. The End.',
    },
  ];

  const currentStory = storyPages[currentPage];

  return (
    <WorkspaceLayout>
      <Box p={6} minH="100vh" bg="#080B0A">
        {/* Header */}
        <Flex align="center" justify="space-between" mb={6}>
          <Box>
            <Flex align="center" gap={3} mb={1}>
              <FiBookOpen size={24} color="#B7FF35" />
              <Heading size="lg" color="#F4F7F0" fontWeight="700">
                Storybook Studio
              </Heading>
            </Flex>
            <Text color="#A5B1A7" fontSize="sm">
              Create magical stories with AI-generated illustrations and narratives
            </Text>
          </Box>
          <HStack spacing={2}>
            <Button
              size="sm"
              variant="outline"
              borderColor="#2A3A2C"
              color="#A5B1A7"
              _hover={{ bg: '#1A2A1C', borderColor: '#B7FF35', color: '#F4F7F0' }}
              leftIcon={<FiShare2 size={14} />}
              fontSize="xs"
            >
              Share
            </Button>
            <Button
              size="sm"
              variant="outline"
              borderColor="#2A3A2C"
              color="#A5B1A7"
              _hover={{ bg: '#1A2A1C', borderColor: '#B7FF35', color: '#F4F7F0' }}
              leftIcon={<FiDownload size={14} />}
              fontSize="xs"
            >
              Export PDF
            </Button>
          </HStack>
        </Flex>

        {/* Main Layout */}
        <Flex gap={6} h="calc(100vh - 160px)">
          {/* Left Panel: Story Configuration */}
          <Box
            w="360px"
            minW="360px"
            bg="#111713"
            borderRadius="xl"
            border="1px solid #2A3A2C"
            p={6}
            overflowY="auto"
            css={{
              '&::-webkit-scrollbar': { width: '4px' },
              '&::-webkit-scrollbar-track': { bg: 'transparent' },
              '&::-webkit-scrollbar-thumb': {
                bg: '#2A3A2C',
                borderRadius: '4px',
              },
            }}
          >
            <VStack spacing={5} align="stretch">
              {/* Section Header */}
              <Flex align="center" gap={2}>
                <FiEdit3 size={16} color="#B7FF35" />
                <Text
                  color="#F4F7F0"
                  fontSize="sm"
                  fontWeight="700"
                >
                  Story Configuration
                </Text>
              </Flex>

              {/* Story Title */}
              <Box>
                <Text color="#A5B1A7" fontSize="xs" fontWeight="600" mb={2}>
                  Story Title
                </Text>
                <Input
                  value={storyTitle}
                  onChange={(e) => setStoryTitle(e.target.value)}
                  bg="#0F1A11"
                  border="1px solid #2A3A2C"
                  borderRadius="lg"
                  color="#F4F7F0"
                  fontSize="sm"
                  _placeholder={{ color: '#A5B1A7' }}
                  _hover={{ borderColor: '#B7FF35' }}
                  _focus={{
                    borderColor: '#B7FF35',
                    boxShadow: '0 0 0 1px #B7FF35',
                  }}
                  placeholder="Enter your story title..."
                />
              </Box>

              {/* Story Idea */}
              <Box>
                <Text color="#A5B1A7" fontSize="xs" fontWeight="600" mb={2}>
                  Story Idea / Description
                </Text>
                <Textarea
                  value={storyIdea}
                  onChange={(e) => setStoryIdea(e.target.value)}
                  bg="#0F1A11"
                  border="1px solid #2A3A2C"
                  borderRadius="lg"
                  color="#F4F7F0"
                  fontSize="sm"
                  rows={5}
                  resize="none"
                  _placeholder={{ color: '#A5B1A7' }}
                  _hover={{ borderColor: '#B7FF35' }}
                  _focus={{
                    borderColor: '#B7FF35',
                    boxShadow: '0 0 0 1px #B7FF35',
                  }}
                  placeholder="Describe your story idea..."
                />
              </Box>

              {/* Style */}
              <Box>
                <Text color="#A5B1A7" fontSize="xs" fontWeight="600" mb={2}>
                  Illustration Style
                </Text>
                <Select
                  value={style}
                  onChange={(e) => setStyle(e.target.value)}
                  bg="#0F1A11"
                  border="1px solid #2A3A2C"
                  borderRadius="lg"
                  color="#F4F7F0"
                  fontSize="sm"
                  _hover={{ borderColor: '#B7FF35' }}
                  _focus={{
                    borderColor: '#B7FF35',
                    boxShadow: '0 0 0 1px #B7FF35',
                  }}
                >
                  <option value="children" style={{ background: '#111713' }}>
                    Children&apos;s Illustration
                  </option>
                  <option value="comic" style={{ background: '#111713' }}>
                    Comic Book
                  </option>
                  <option value="watercolor" style={{ background: '#111713' }}>
                    Watercolor
                  </option>
                  <option value="pixel" style={{ background: '#111713' }}>
                    Pixel Art
                  </option>
                  <option value="anime" style={{ background: '#111713' }}>
                    Anime / Manga
                  </option>
                  <option value="storybook" style={{ background: '#111713' }}>
                    Classic Storybook
                  </option>
                </Select>
              </Box>

              {/* Page Count */}
              <Box>
                <Text color="#A5B1A7" fontSize="xs" fontWeight="600" mb={3}>
                  Number of Pages
                </Text>
                <HStack spacing={2}>
                  {[4, 6, 8, 12].map((count) => (
                    <Button
                      key={count}
                      size="sm"
                      flex={1}
                      bg={pageCount === count ? '#B7FF35' : '#0F1A11'}
                      color={pageCount === count ? '#080B0A' : '#A5B1A7'}
                      border="1px solid"
                      borderColor={pageCount === count ? '#B7FF35' : '#2A3A2C'}
                      borderRadius="lg"
                      fontWeight={pageCount === count ? '700' : '500'}
                      fontSize="sm"
                      _hover={{
                        bg: pageCount === count ? '#8DDB39' : '#1A2A1C',
                        borderColor: '#B7FF35',
                      }}
                      onClick={() => setPageCount(count)}
                      transition="all 0.2s"
                    >
                      {count}
                    </Button>
                  ))}
                </HStack>
              </Box>

              <Divider borderColor="#2A3A2C" />

              {/* Create Button */}
              <Button
                bg="#B7FF35"
                color="#080B0A"
                size="lg"
                borderRadius="xl"
                fontWeight="700"
                fontSize="sm"
                _hover={{
                  bg: '#8DDB39',
                  transform: 'translateY(-2px)',
                  boxShadow: '0 8px 30px rgba(183,255,53,0.3)',
                }}
                _active={{ transform: 'translateY(0)' }}
                transition="all 0.2s"
                boxShadow="0 4px 20px rgba(183,255,53,0.2)"
                h="50px"
              >
                ✨ Create Storybook
              </Button>

              {/* Stats */}
              <Flex
                bg="#0F1A11"
                borderRadius="lg"
                p={3}
                justify="space-around"
                border="1px solid #2A3A2C"
              >
                <VStack spacing={0}>
                  <Text color="#B7FF35" fontSize="lg" fontWeight="700">
                    {pageCount}
                  </Text>
                  <Text color="#A5B1A7" fontSize="10px">
                    Pages
                  </Text>
                </VStack>
                <Divider
                  orientation="vertical"
                  h="36px"
                  borderColor="#2A3A2C"
                />
                <VStack spacing={0}>
                  <Text color="#B7FF35" fontSize="lg" fontWeight="700">
                    {pageCount}
                  </Text>
                  <Text color="#A5B1A7" fontSize="10px">
                    Images
                  </Text>
                </VStack>
                <Divider
                  orientation="vertical"
                  h="36px"
                  borderColor="#2A3A2C"
                />
                <VStack spacing={0}>
                  <Text color="#B7FF35" fontSize="lg" fontWeight="700">
                    ~2m
                  </Text>
                  <Text color="#A5B1A7" fontSize="10px">
                    Est. Time
                  </Text>
                </VStack>
              </Flex>
            </VStack>
          </Box>

          {/* Right Panel: Preview */}
          <Box
            flex={1}
            bg="#111713"
            borderRadius="xl"
            border="1px solid #2A3A2C"
            display="flex"
            flexDir="column"
            overflow="hidden"
          >
            {/* Preview Header */}
            <Flex
              align="center"
              justify="space-between"
              px={6}
              py={3}
              borderBottom="1px solid #2A3A2C"
            >
              <Flex align="center" gap={2}>
                <FiBookOpen size={14} color="#B7FF35" />
                <Text color="#F4F7F0" fontSize="sm" fontWeight="600">
                  Preview
                </Text>
                <Badge
                  bg="rgba(183,255,53,0.1)"
                  color="#B7FF35"
                  fontSize="10px"
                  borderRadius="full"
                  px={2}
                >
                  Live
                </Badge>
              </Flex>
              <Text color="#A5B1A7" fontSize="xs">
                {storyTitle}
              </Text>
            </Flex>

            {/* Book Preview Area */}
            <Flex
              flex={1}
              align="center"
              justify="center"
              p={8}
              bg="radial-gradient(ellipse at center, #182019 0%, #111713 70%)"
            >
              <Box
                maxW="520px"
                w="100%"
                bg="#182019"
                borderRadius="2xl"
                overflow="hidden"
                border="1px solid #2A3A2C"
                boxShadow="0 20px 60px rgba(0,0,0,0.5), 0 0 40px rgba(183,255,53,0.03)"
              >
                {/* Book Image */}
                <Box position="relative" overflow="hidden">
                  <Image
                    src={currentStory?.image}
                    alt={`Page ${currentPage + 1}`}
                    w="100%"
                    h="280px"
                    objectFit="cover"
                  />
                  {/* Page number overlay */}
                  <Box
                    position="absolute"
                    top={3}
                    right={3}
                    bg="rgba(8,11,10,0.7)"
                    px={3}
                    py={1}
                    borderRadius="full"
                    backdropFilter="blur(10px)"
                  >
                    <Text color="#B7FF35" fontSize="10px" fontWeight="700">
                      {currentPage + 1} / {storyPages.length}
                    </Text>
                  </Box>
                </Box>

                {/* Book Text */}
                <Box p={6}>
                  {currentPage === 0 && (
                    <Text
                      color="#B7FF35"
                      fontSize="lg"
                      fontWeight="700"
                      mb={3}
                      lineHeight="1.3"
                    >
                      {storyTitle}
                    </Text>
                  )}
                  <Text
                    color="#F4F7F0"
                    fontSize="sm"
                    lineHeight="1.8"
                    fontStyle={currentPage === storyPages.length - 1 ? 'italic' : 'normal'}
                  >
                    {currentStory?.text}
                  </Text>
                </Box>

                {/* Navigation */}
                <Flex
                  align="center"
                  justify="space-between"
                  px={6}
                  py={4}
                  borderTop="1px solid #2A3A2C"
                >
                  <IconButton
                    aria-label="Previous page"
                    icon={<FiChevronLeft size={18} />}
                    size="sm"
                    bg={currentPage > 0 ? '#0F1A11' : 'transparent'}
                    color={currentPage > 0 ? '#F4F7F0' : '#2A3A2C'}
                    border="1px solid"
                    borderColor={currentPage > 0 ? '#2A3A2C' : 'transparent'}
                    borderRadius="lg"
                    _hover={
                      currentPage > 0
                        ? { bg: '#1A2A1C', borderColor: '#B7FF35' }
                        : {}
                    }
                    onClick={() =>
                      setCurrentPage(Math.max(0, currentPage - 1))
                    }
                    isDisabled={currentPage === 0}
                  />
                  <HStack spacing={1.5}>
                    {storyPages.map((_, idx) => (
                      <Box
                        key={idx}
                        w={currentPage === idx ? '20px' : '6px'}
                        h="6px"
                        bg={currentPage === idx ? '#B7FF35' : '#2A3A2C'}
                        borderRadius="full"
                        cursor="pointer"
                        onClick={() => setCurrentPage(idx)}
                        transition="all 0.3s ease"
                        _hover={{ bg: '#8DDB39' }}
                      />
                    ))}
                  </HStack>
                  <IconButton
                    aria-label="Next page"
                    icon={<FiChevronRight size={18} />}
                    size="sm"
                    bg={
                      currentPage < storyPages.length - 1
                        ? '#0F1A11'
                        : 'transparent'
                    }
                    color={
                      currentPage < storyPages.length - 1
                        ? '#F4F7F0'
                        : '#2A3A2C'
                    }
                    border="1px solid"
                    borderColor={
                      currentPage < storyPages.length - 1
                        ? '#2A3A2C'
                        : 'transparent'
                    }
                    borderRadius="lg"
                    _hover={
                      currentPage < storyPages.length - 1
                        ? { bg: '#1A2A1C', borderColor: '#B7FF35' }
                        : {}
                    }
                    onClick={() =>
                      setCurrentPage(
                        Math.min(storyPages.length - 1, currentPage + 1)
                      )
                    }
                    isDisabled={currentPage === storyPages.length - 1}
                  />
                </Flex>
              </Box>
            </Flex>

            {/* Bottom Bar */}
            <Flex
              align="center"
              justify="center"
              px={6}
              py={3}
              borderTop="1px solid #2A3A2C"
              bg="#0D120E"
            >
              <Text color="#A5B1A7" fontSize="xs">
                Page {currentPage + 1} of {storyPages.length} •{' '}
                <Text as="span" color="#B7FF35">
                  Children&apos;s Illustration
                </Text>{' '}
                style
              </Text>
            </Flex>
          </Box>
        </Flex>
      </Box>
    </WorkspaceLayout>
  );
};

export default StoryBookStudio;
