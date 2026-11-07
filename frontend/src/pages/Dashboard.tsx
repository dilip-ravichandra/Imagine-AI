import React from 'react';
import {
  Box,
  Flex,
  Grid,
  GridItem,
  Text,
  Heading,
  Image,
  Badge,
  Icon,
} from '@chakra-ui/react';
import { Link } from 'react-router-dom';
import WorkspaceLayout from '../components/WorkspaceLayout';

const quickActions = [
  {
    icon: '🎨',
    title: 'Create Studio',
    description: 'Multimodal chat, voice prompts & selective recreate',
    route: '/create',
    gradient: 'linear(to-br, #1a2a1c, #111713)',
  },
  {
    icon: '📖',
    title: 'Storybook & Comics',
    description: 'Illustrated multi-scene books & graphic novels',
    route: '/storybook',
    gradient: 'linear(to-br, #1a2a1c, #111713)',
  },
  {
    icon: '📚',
    title: 'Learning Studio',
    description: 'Visual diagrams & educational explanations',
    route: '/learn',
    gradient: 'linear(to-br, #1a2a1c, #111713)',
  },
  {
    icon: '✏️',
    title: 'Image Editor',
    description: 'Inpaint, remove objects & enhance images',
    route: '/edit',
    gradient: 'linear(to-br, #1a2a1c, #111713)',
  },
];

const recentCreations = [
  { id: 1, seed: 'cybercity', label: 'Cyber City at Dusk', prompt: 'A futuristic cyber city...' },
  { id: 2, seed: 'forest42', label: 'Enchanted Forest', prompt: 'Magical forest with...' },
  { id: 3, seed: 'portrait7', label: 'Digital Portrait', prompt: 'Hyper-realistic portrait...' },
  { id: 4, seed: 'space99', label: 'Nebula Dreams', prompt: 'Deep space nebula...' },
  { id: 5, seed: 'ocean23', label: 'Ocean Depths', prompt: 'Underwater coral reef...' },
  { id: 6, seed: 'mountain1', label: 'Alpine Sunrise', prompt: 'Mountain peak at sunrise...' },
];

const favorites = [
  { id: 1, seed: 'fav1', label: 'Neon Samurai' },
  { id: 2, seed: 'fav2', label: 'Crystal Cave' },
  { id: 3, seed: 'fav3', label: 'Steampunk Owl' },
  { id: 4, seed: 'fav4', label: 'Aurora City' },
];

const Dashboard: React.FC = () => {
  return (
    <WorkspaceLayout>
      <Box px={{ base: 4, md: 8 }} py={8} maxW="1400px" mx="auto">
        {/* Welcome Header */}
        <Box mb={10}>
          <Heading
            fontSize={{ base: '2xl', md: '3xl' }}
            fontWeight="700"
            color="#F4F7F0"
            mb={2}
          >
            Welcome back, Dilip 👋
          </Heading>
          <Text fontSize="lg" color="#A5B1A7">
            What would you like to create today?
          </Text>
        </Box>

        {/* Quick Actions */}
        <Grid
          templateColumns={{ base: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)' }}
          gap={5}
          mb={12}
        >
          {quickActions.map((action) => (
            <GridItem key={action.title}>
              <Link to={action.route} style={{ textDecoration: 'none' }}>
                <Box
                  bg="#111713"
                  border="1px solid"
                  borderColor="#2A3A2C"
                  borderRadius="12px"
                  p={6}
                  cursor="pointer"
                  transition="all 0.25s cubic-bezier(0.4, 0, 0.2, 1)"
                  _hover={{
                    borderColor: '#B7FF35',
                    boxShadow: '0 0 20px rgba(183, 255, 53, 0.15), 0 0 40px rgba(183, 255, 53, 0.05)',
                    transform: 'translateY(-3px)',
                    bg: '#182019',
                  }}
                  position="relative"
                  overflow="hidden"
                >
                  <Box
                    position="absolute"
                    top="-20px"
                    right="-20px"
                    w="80px"
                    h="80px"
                    borderRadius="50%"
                    bg="radial-gradient(circle, rgba(183,255,53,0.06) 0%, transparent 70%)"
                    pointerEvents="none"
                  />
                  <Text fontSize="2xl" mb={3}>
                    {action.icon}
                  </Text>
                  <Heading fontSize="md" color="#F4F7F0" fontWeight="600" mb={1}>
                    {action.title}
                  </Heading>
                  <Text fontSize="sm" color="#A5B1A7" lineHeight="1.5">
                    {action.description}
                  </Text>
                </Box>
              </Link>
            </GridItem>
          ))}
        </Grid>

        {/* Recent Creations */}
        <Box mb={12}>
          <Flex justify="space-between" align="center" mb={5}>
            <Heading fontSize="xl" color="#F4F7F0" fontWeight="600">
              Recent Creations
            </Heading>
            <Link to="/gallery" style={{ textDecoration: 'none' }}>
              <Text
                fontSize="sm"
                color="#B7FF35"
                cursor="pointer"
                _hover={{ textDecoration: 'underline' }}
              >
                View all →
              </Text>
            </Link>
          </Flex>
          <Grid
            templateColumns={{ base: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' }}
            gap={5}
          >
            {recentCreations.map((item) => (
              <GridItem key={item.id}>
                <Box
                  borderRadius="12px"
                  overflow="hidden"
                  position="relative"
                  cursor="pointer"
                  transition="all 0.25s ease"
                  _hover={{
                    transform: 'scale(1.03)',
                    boxShadow: '0 8px 30px rgba(0,0,0,0.4)',
                  }}
                  bg="#111713"
                  border="1px solid"
                  borderColor="#2A3A2C"
                >
                  <Image
                    src={`https://picsum.photos/seed/${item.seed}/300/300`}
                    alt={item.label}
                    w="100%"
                    h="220px"
                    objectFit="cover"
                  />
                  <Box
                    position="absolute"
                    bottom={0}
                    left={0}
                    right={0}
                    bgGradient="linear(to-t, rgba(0,0,0,0.85), transparent)"
                    p={4}
                    pt={10}
                  >
                    <Text
                      fontSize="sm"
                      fontWeight="600"
                      color="#F4F7F0"
                    >
                      {item.label}
                    </Text>
                    <Text fontSize="xs" color="#A5B1A7" noOfLines={1}>
                      {item.prompt}
                    </Text>
                  </Box>
                  <Badge
                    position="absolute"
                    top={3}
                    right={3}
                    bg="rgba(183,255,53,0.15)"
                    color="#B7FF35"
                    fontSize="10px"
                    px={2}
                    py={0.5}
                    borderRadius="6px"
                    fontWeight="500"
                  >
                    SD-Turbo
                  </Badge>
                </Box>
              </GridItem>
            ))}
          </Grid>
        </Box>

        {/* Favorites */}
        <Box mb={8}>
          <Flex justify="space-between" align="center" mb={5}>
            <Heading fontSize="xl" color="#F4F7F0" fontWeight="600">
              ⭐ Favorites
            </Heading>
            <Link to="/gallery" style={{ textDecoration: 'none' }}>
              <Text
                fontSize="sm"
                color="#B7FF35"
                cursor="pointer"
                _hover={{ textDecoration: 'underline' }}
              >
                Manage →
              </Text>
            </Link>
          </Flex>
          <Grid
            templateColumns={{ base: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }}
            gap={4}
          >
            {favorites.map((fav) => (
              <GridItem key={fav.id}>
                <Box
                  borderRadius="12px"
                  overflow="hidden"
                  position="relative"
                  cursor="pointer"
                  transition="all 0.25s ease"
                  _hover={{
                    transform: 'scale(1.04)',
                    boxShadow: '0 0 16px rgba(183,255,53,0.12)',
                    borderColor: '#B7FF35',
                  }}
                  border="1px solid"
                  borderColor="#2A3A2C"
                >
                  <Image
                    src={`https://picsum.photos/seed/${fav.seed}/300/300`}
                    alt={fav.label}
                    w="100%"
                    h="160px"
                    objectFit="cover"
                  />
                  <Box
                    position="absolute"
                    bottom={0}
                    left={0}
                    right={0}
                    bgGradient="linear(to-t, rgba(0,0,0,0.8), transparent)"
                    px={3}
                    py={2}
                    pt={6}
                  >
                    <Text fontSize="xs" fontWeight="600" color="#F4F7F0">
                      {fav.label}
                    </Text>
                  </Box>
                  <Box
                    position="absolute"
                    top={2}
                    right={2}
                    bg="rgba(0,0,0,0.5)"
                    borderRadius="full"
                    w="26px"
                    h="26px"
                    display="flex"
                    alignItems="center"
                    justifyContent="center"
                    fontSize="12px"
                  >
                    ⭐
                  </Box>
                </Box>
              </GridItem>
            ))}
          </Grid>
        </Box>
      </Box>
    </WorkspaceLayout>
  );
};

export default Dashboard;
