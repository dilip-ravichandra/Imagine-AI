import React, { useState } from 'react';
import {
  Box,
  Flex,
  Grid,
  GridItem,
  Text,
  Heading,
  Input,
  InputGroup,
  InputLeftElement,
  Button,
  Image,
  Select,
  HStack,
  VStack,
} from '@chakra-ui/react';
import { SearchIcon } from '@chakra-ui/icons';
import WorkspaceLayout from '../components/WorkspaceLayout';

const ageLevels = [
  { label: 'Kids (5-8)', value: 'kids' },
  { label: 'Students (9-14)', value: 'students' },
  { label: 'Advanced (15+)', value: 'advanced' },
];

interface Topic {
  id: number;
  icon: string;
  title: string;
  description: string;
  seed: string;
  explanation: string;
}

const featuredTopics: Topic[] = [
  {
    id: 1,
    icon: '🌍',
    title: 'Solar System',
    description: 'Explore our cosmic neighborhood — planets, moons, and beyond.',
    seed: 'solarsystem',
    explanation:
      'The Solar System consists of the Sun and the celestial objects bound to it by gravity. Eight planets orbit the Sun in nearly circular paths: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune. The inner planets are rocky, while the outer gas giants are massive and composed largely of hydrogen and helium. Between Mars and Jupiter lies the asteroid belt, and beyond Neptune stretches the Kuiper Belt, home to dwarf planets like Pluto. The Sun contains 99.86% of the system\'s total mass and drives all planetary motion through its immense gravitational pull.',
  },
  {
    id: 2,
    icon: '🫀',
    title: 'Human Body',
    description: 'Discover the amazing systems that keep you alive and healthy.',
    seed: 'humanbody',
    explanation:
      'The human body is an intricate biological machine composed of 11 major organ systems working in harmony. The circulatory system, powered by the heart, pumps blood through 60,000 miles of blood vessels. The nervous system processes millions of signals per second through 86 billion neurons. Your skeletal system comprises 206 bones providing structure and protection, while over 600 muscles enable movement. The digestive system breaks down food through a 30-foot journey, and the immune system deploys specialized cells to defend against pathogens.',
  },
  {
    id: 3,
    icon: '🌱',
    title: 'Plant Life Cycle',
    description: 'From tiny seeds to towering trees — the miracle of plant growth.',
    seed: 'plantlife',
    explanation:
      'The plant life cycle begins with a seed that contains a tiny embryo and stored nutrients. When conditions are right — adequate water, warmth, and oxygen — germination occurs and a root emerges downward while a shoot reaches for sunlight. Through photosynthesis, the plant converts carbon dioxide and water into glucose using sunlight energy captured by chlorophyll. As the plant matures, it develops flowers containing male stamens and female pistils. Pollination occurs via wind, insects, or birds, leading to fertilization and seed production, completing the cycle.',
  },
  {
    id: 4,
    icon: '💧',
    title: 'Water Cycle',
    description: 'Follow water\'s endless journey through Earth\'s atmosphere.',
    seed: 'watercycle',
    explanation:
      'The water cycle, or hydrological cycle, describes the continuous movement of water through Earth\'s systems. Solar energy heats surface water in oceans, lakes, and rivers, causing evaporation — the transformation from liquid to water vapor. Plants contribute through transpiration, releasing moisture through their leaves. As warm, moist air rises, it cools and condenses around tiny particles to form clouds. When water droplets combine and grow heavy enough, precipitation occurs as rain, snow, sleet, or hail. Water then flows as runoff into streams and rivers, or infiltrates the ground to replenish aquifers.',
  },
];

const LearnStudio: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [ageLevel, setAgeLevel] = useState('students');
  const [complexity, setComplexity] = useState('Moderate');
  const [selectedTopic, setSelectedTopic] = useState<Topic | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);

  const handleTopicClick = (topic: Topic) => {
    setSelectedTopic(topic);
    setShowExplanation(false);
  };

  const handleGenerate = () => {
    if (!selectedTopic && !searchTerm.trim()) return;
    setIsGenerating(true);
    setShowExplanation(false);

    setTimeout(() => {
      if (!selectedTopic && searchTerm.trim()) {
        setSelectedTopic({
          id: 99,
          icon: '🔬',
          title: searchTerm,
          description: `Exploring ${searchTerm} in depth`,
          seed: `custom${Date.now()}`,
          explanation: `${searchTerm} is a fascinating topic that encompasses many interconnected concepts. At the ${complexity.toLowerCase()} level, we can explore the fundamental principles that govern this subject, examining both the theoretical framework and practical applications that make it relevant to everyday life. Understanding ${searchTerm} helps us appreciate the complexity and beauty of the world around us.`,
        });
      }
      setIsGenerating(false);
      setShowExplanation(true);
    }, 2000);
  };

  const filteredTopics = featuredTopics.filter((t) =>
    t.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <WorkspaceLayout>
      <Box px={{ base: 4, md: 8 }} py={8} maxW="1400px" mx="auto">
        {/* Header */}
        <Box mb={8}>
          <Flex align="center" gap={3} mb={2}>
            <Box
              w="40px"
              h="40px"
              borderRadius="10px"
              bg="rgba(183,255,53,0.1)"
              display="flex"
              alignItems="center"
              justifyContent="center"
              fontSize="xl"
            >
              📚
            </Box>
            <Box>
              <Heading fontSize="2xl" color="#F4F7F0" fontWeight="700">
                Learning Studio
              </Heading>
              <Text fontSize="sm" color="#A5B1A7">
                Visual learning for everyone
              </Text>
            </Box>
          </Flex>
        </Box>

        {/* Search Bar */}
        <InputGroup mb={6} maxW="700px">
          <InputLeftElement h="48px" pointerEvents="none">
            <SearchIcon color="#A5B1A7" />
          </InputLeftElement>
          <Input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search a topic (e.g., Solar System, Human Body...)"
            h="48px"
            bg="#0F1A11"
            color="#F4F7F0"
            border="1px solid"
            borderColor="#2A3A2C"
            borderRadius="12px"
            fontSize="sm"
            pl="44px"
            _placeholder={{ color: '#5a6b5c' }}
            _hover={{ borderColor: '#8DDB39' }}
            _focus={{
              borderColor: '#B7FF35',
              boxShadow: '0 0 0 1px #B7FF35',
            }}
          />
        </InputGroup>

        {/* Age Level Tabs */}
        <HStack spacing={3} mb={8}>
          {ageLevels.map((level) => (
            <Button
              key={level.value}
              size="sm"
              h="36px"
              px={5}
              borderRadius="full"
              fontWeight="600"
              fontSize="sm"
              bg={ageLevel === level.value ? '#B7FF35' : '#111713'}
              color={ageLevel === level.value ? '#080B0A' : '#A5B1A7'}
              border="1px solid"
              borderColor={ageLevel === level.value ? '#B7FF35' : '#2A3A2C'}
              _hover={{
                bg: ageLevel === level.value ? '#8DDB39' : '#1A2A1C',
                borderColor: '#B7FF35',
              }}
              transition="all 0.2s ease"
              onClick={() => setAgeLevel(level.value)}
            >
              {level.label}
            </Button>
          ))}
        </HStack>

        {/* Featured Topics */}
        <Box mb={10}>
          <Heading fontSize="lg" color="#F4F7F0" fontWeight="600" mb={4}>
            Featured Topics
          </Heading>
          <Grid
            templateColumns={{ base: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)' }}
            gap={5}
          >
            {filteredTopics.map((topic) => (
              <GridItem key={topic.id}>
                <Box
                  bg="#111713"
                  border="2px solid"
                  borderColor={
                    selectedTopic?.id === topic.id ? '#B7FF35' : '#2A3A2C'
                  }
                  borderRadius="14px"
                  overflow="hidden"
                  cursor="pointer"
                  transition="all 0.25s cubic-bezier(0.4, 0, 0.2, 1)"
                  _hover={{
                    borderColor: '#B7FF35',
                    transform: 'translateY(-3px)',
                    boxShadow:
                      '0 0 20px rgba(183,255,53,0.12), 0 8px 24px rgba(0,0,0,0.3)',
                  }}
                  onClick={() => handleTopicClick(topic)}
                >
                  <Image
                    src={`https://picsum.photos/seed/${topic.seed}/400/200`}
                    alt={topic.title}
                    w="100%"
                    h="130px"
                    objectFit="cover"
                  />
                  <Box p={4}>
                    <Flex align="center" gap={2} mb={1}>
                      <Text fontSize="lg">{topic.icon}</Text>
                      <Heading fontSize="sm" color="#F4F7F0" fontWeight="600">
                        {topic.title}
                      </Heading>
                    </Flex>
                    <Text fontSize="xs" color="#A5B1A7" lineHeight="1.5">
                      {topic.description}
                    </Text>
                  </Box>
                  {selectedTopic?.id === topic.id && (
                    <Box
                      h="3px"
                      bg="#B7FF35"
                      borderRadius="full"
                      mx={4}
                      mb={3}
                    />
                  )}
                </Box>
              </GridItem>
            ))}
          </Grid>
        </Box>

        {/* Controls Row */}
        <Flex
          gap={4}
          mb={6}
          align="flex-end"
          direction={{ base: 'column', sm: 'row' }}
        >
          <Box flex={1} maxW="260px">
            <Text
              fontSize="xs"
              fontWeight="600"
              color="#A5B1A7"
              mb={1.5}
              textTransform="uppercase"
              letterSpacing="0.05em"
            >
              Complexity
            </Text>
            <Select
              value={complexity}
              onChange={(e) => setComplexity(e.target.value)}
              bg="#0F1A11"
              color="#F4F7F0"
              border="1px solid"
              borderColor="#2A3A2C"
              borderRadius="10px"
              fontSize="sm"
              _hover={{ borderColor: '#8DDB39' }}
              _focus={{
                borderColor: '#B7FF35',
                boxShadow: '0 0 0 1px #B7FF35',
              }}
              sx={{
                option: { bg: '#111713', color: '#F4F7F0' },
              }}
            >
              <option value="Simple">Simple</option>
              <option value="Moderate">Moderate</option>
              <option value="Detailed">Detailed</option>
            </Select>
          </Box>
          <Button
            h="42px"
            px={8}
            bg="#B7FF35"
            color="#080B0A"
            borderRadius="10px"
            fontWeight="700"
            fontSize="sm"
            _hover={{
              bg: '#8DDB39',
              transform: 'translateY(-1px)',
              boxShadow: '0 4px 16px rgba(183,255,53,0.3)',
            }}
            _active={{ transform: 'scale(0.98)' }}
            transition="all 0.2s ease"
            onClick={handleGenerate}
            isLoading={isGenerating}
            loadingText="Generating..."
            isDisabled={!selectedTopic && !searchTerm.trim()}
          >
            ✨ Generate Visual Explanation
          </Button>
        </Flex>

        {/* Generated Explanation */}
        {showExplanation && selectedTopic && (
          <Box
            bg="#111713"
            border="1px solid"
            borderColor="#2A3A2C"
            borderRadius="16px"
            overflow="hidden"
            sx={{
              animation: 'fadeSlideIn 0.5s ease-out',
              '@keyframes fadeSlideIn': {
                '0%': { opacity: 0, transform: 'translateY(16px)' },
                '100%': { opacity: 1, transform: 'translateY(0)' },
              },
            }}
          >
            <Flex direction={{ base: 'column', md: 'row' }}>
              {/* Image */}
              <Box
                w={{ base: '100%', md: '360px' }}
                minH={{ base: '200px', md: '280px' }}
                flexShrink={0}
              >
                <Image
                  src={`https://picsum.photos/seed/${selectedTopic.seed}vis/600/400`}
                  alt={selectedTopic.title}
                  w="100%"
                  h="100%"
                  objectFit="cover"
                />
              </Box>

              {/* Explanation */}
              <Box p={7} flex={1}>
                <Flex align="center" gap={2} mb={3}>
                  <Text fontSize="xl">{selectedTopic.icon}</Text>
                  <Heading fontSize="lg" color="#F4F7F0" fontWeight="700">
                    {selectedTopic.title}
                  </Heading>
                  <Box
                    ml="auto"
                    bg="rgba(183,255,53,0.1)"
                    px={3}
                    py={1}
                    borderRadius="full"
                  >
                    <Text fontSize="xs" color="#B7FF35" fontWeight="600">
                      {ageLevels.find((l) => l.value === ageLevel)?.label}
                    </Text>
                  </Box>
                </Flex>
                <Box
                  h="1px"
                  bg="#2A3A2C"
                  mb={4}
                />
                <Text
                  fontSize="sm"
                  color="#F4F7F0"
                  lineHeight="1.8"
                  mb={4}
                >
                  {selectedTopic.explanation}
                </Text>
                <Flex
                  gap={3}
                  pt={2}
                  borderTop="1px solid"
                  borderColor="#2A3A2C"
                >
                  <Box
                    bg="rgba(183,255,53,0.08)"
                    px={3}
                    py={1.5}
                    borderRadius="8px"
                  >
                    <Text fontSize="xs" color="#8DDB39" fontWeight="600">
                      📊 {complexity} detail
                    </Text>
                  </Box>
                  <Box
                    bg="rgba(183,255,53,0.08)"
                    px={3}
                    py={1.5}
                    borderRadius="8px"
                  >
                    <Text fontSize="xs" color="#8DDB39" fontWeight="600">
                      🤖 AI Generated
                    </Text>
                  </Box>
                </Flex>
              </Box>
            </Flex>
          </Box>
        )}

        {/* Empty state when no topic selected */}
        {!showExplanation && !isGenerating && (
          <Box
            bg="#111713"
            border="1px dashed"
            borderColor="#2A3A2C"
            borderRadius="16px"
            p={10}
            textAlign="center"
          >
            <Text fontSize="3xl" mb={3}>
              🔍
            </Text>
            <Text fontSize="sm" color="#A5B1A7" maxW="340px" mx="auto" lineHeight="1.6">
              Select a topic above or search for any subject, then click
              &quot;Generate Visual Explanation&quot; to create an interactive learning experience.
            </Text>
          </Box>
        )}

        {/* Generating state */}
        {isGenerating && (
          <Box
            bg="#111713"
            border="1px solid"
            borderColor="#2A3A2C"
            borderRadius="16px"
            p={10}
            textAlign="center"
          >
            <Box
              display="inline-flex"
              alignItems="center"
              justifyContent="center"
              w="56px"
              h="56px"
              borderRadius="14px"
              bg="rgba(183,255,53,0.08)"
              mb={4}
              sx={{
                animation: 'pulse 1.8s ease-in-out infinite',
                '@keyframes pulse': {
                  '0%, 100%': { transform: 'scale(1)', opacity: 0.7 },
                  '50%': { transform: 'scale(1.12)', opacity: 1 },
                },
              }}
            >
              <Text fontSize="2xl">🧠</Text>
            </Box>
            <Text fontSize="sm" color="#A5B1A7" fontWeight="500">
              Generating visual explanation...
            </Text>
          </Box>
        )}
      </Box>
    </WorkspaceLayout>
  );
};

export default LearnStudio;
