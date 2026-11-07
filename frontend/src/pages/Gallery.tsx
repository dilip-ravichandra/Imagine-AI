import React, { useState } from 'react';
import {
  Box,
  Flex,
  Text,
  Heading,
  Button,
  Input,
  Grid,
  GridItem,
  InputGroup,
  InputLeftElement,
  Badge,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  HStack,
  IconButton,
} from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';
import WorkspaceLayout from '../components/WorkspaceLayout';

const SearchIcon: React.FC = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#A5B1A7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
  </svg>
);

const HeartIcon: React.FC<{ filled?: boolean }> = ({ filled }) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill={filled ? '#FF4444' : 'none'} stroke={filled ? '#FF4444' : '#F4F7F0'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
  </svg>
);

const DownloadIcon: React.FC = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#F4F7F0" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" />
  </svg>
);

interface ImageCard {
  id: number;
  seed: number;
  prompt: string;
  category: 'Single' | 'Storybook' | 'Selective Inpaint';
  model: string;
  date: string;
  liked: boolean;
}

const IMAGES: ImageCard[] = [
  { id: 1, seed: 10, prompt: 'A futuristic city with green energy, at sunset, cinematic, ultra realistic', category: 'Single', model: 'SD-Turbo', date: 'Just now', liked: true },
  { id: 2, seed: 22, prompt: 'Cyberpunk city street with neon reflections on wet pavement', category: 'Single', model: 'SD-Turbo', date: 'Nov 6, 2026', liked: true },
  { id: 3, seed: 33, prompt: 'The Little Robot: Scene 1 - Walking through the shimmering sunrise avenues', category: 'Storybook', model: 'Pixar 3D', date: 'Nov 6, 2026', liked: false },
  { id: 4, seed: 44, prompt: 'The Little Robot: Scene 2 - Discovering the kitten behind the solar recycle post', category: 'Storybook', model: 'Pixar 3D', date: 'Nov 6, 2026', liked: true },
  { id: 5, seed: 55, prompt: 'Selective Inpaint: Replaced sky with deep violet aurora and shooting stars', category: 'Selective Inpaint', model: 'SD-Turbo Inpaint', date: 'Nov 5, 2026', liked: true },
  { id: 6, seed: 66, prompt: 'Steampunk mechanical owl perched on a brass clock tower', category: 'Single', model: 'Stable Diffusion 1.5', date: 'Nov 5, 2026', liked: false },
  { id: 7, seed: 77, prompt: 'Underwater coral palace with bioluminescent sea turtles and rays', category: 'Single', model: 'MobileDiffusion', date: 'Nov 4, 2026', liked: true },
  { id: 8, seed: 88, prompt: 'Northern lights aurora over a frozen lake with crystal reflection', category: 'Single', model: 'SD-Turbo', date: 'Nov 4, 2026', liked: false },
  { id: 9, seed: 99, prompt: 'The Little Robot: Scene 3 - Sharing the umbrella under neon rain', category: 'Storybook', model: 'Pixar 3D', date: 'Nov 3, 2026', liked: true },
  { id: 10, seed: 111, prompt: 'Selective Inpaint: Added glowing golden visor with cyber reflections', category: 'Selective Inpaint', model: 'SD-Turbo Inpaint', date: 'Nov 3, 2026', liked: false },
  { id: 11, seed: 123, prompt: 'Fantasy castle floating among clouds at golden sunset', category: 'Single', model: 'Stable Diffusion 1.5', date: 'Nov 2, 2026', liked: true },
  { id: 12, seed: 135, prompt: 'Isometric pixel art of a cozy coffee shop with rain outside', category: 'Single', model: 'SD-Turbo', date: 'Nov 1, 2026', liked: false },
];

const TABS = ['All Creations', 'Single Images', 'Storybook Scenes', 'Selective Inpainted', 'Favorites'];

const Gallery: React.FC = () => {
  const [activeTab, setActiveTab] = useState('All Creations');
  const [searchQuery, setSearchQuery] = useState('');
  const [likedImages, setLikedImages] = useState<Set<number>>(
    new Set(IMAGES.filter((img) => img.liked).map((img) => img.id))
  );
  const [hoveredCard, setHoveredCard] = useState<number | null>(null);
  const [inspectImage, setInspectImage] = useState<ImageCard | null>(null);

  const navigate = useNavigate();

  const toggleLike = (id: number) => {
    setLikedImages((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const filteredImages = IMAGES.filter((img) => {
    if (activeTab === 'Favorites' && !likedImages.has(img.id)) return false;
    if (activeTab === 'Single Images' && img.category !== 'Single') return false;
    if (activeTab === 'Storybook Scenes' && img.category !== 'Storybook') return false;
    if (activeTab === 'Selective Inpainted' && img.category !== 'Selective Inpaint') return false;
    if (searchQuery && !img.prompt.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  return (
    <WorkspaceLayout>
      <Box p={8} minH="100vh" bg="#080B0A">
        {/* Header */}
        <Flex align="center" justify="space-between" mb={6}>
          <Box>
            <Flex align="center" gap={2.5}>
              <Heading size="lg" color="#F4F7F0" fontWeight={700}>
                Gallery & Creations Hub
              </Heading>
              <Badge bg="rgba(183, 255, 53, 0.15)" color="#B7FF35" px={2.5} py={0.5} borderRadius="full" fontSize="11px">
                Central Storage
              </Badge>
            </Flex>
            <Text color="#A5B1A7" mt={1} fontSize="sm">
              All generated images, storybook panels, and selective inpaint recreations stored in one place
            </Text>
          </Box>

          <Button
            bg="#B7FF35"
            color="#080B0A"
            fontWeight="bold"
            size="sm"
            onClick={() => navigate('/create')}
            leftIcon={<Text>🎨</Text>}
          >
            Open Generator
          </Button>
        </Flex>

        {/* Tabs */}
        <Flex gap={2} mb={6} overflowX="auto" pb={1}>
          {TABS.map((tab) => (
            <Button
              key={tab}
              onClick={() => setActiveTab(tab)}
              bg={activeTab === tab ? '#B7FF35' : '#111713'}
              color={activeTab === tab ? '#080B0A' : '#A5B1A7'}
              border="1px solid"
              borderColor={activeTab === tab ? '#B7FF35' : '#2A3A2C'}
              borderRadius="10px"
              px={5}
              py={2}
              fontWeight={600}
              fontSize="sm"
              _hover={{
                bg: activeTab === tab ? '#8DDB39' : '#1A2A1C',
                color: activeTab === tab ? '#080B0A' : '#F4F7F0',
              }}
              transition="all 0.2s"
              flexShrink={0}
            >
              {tab}
            </Button>
          ))}
        </Flex>

        {/* Search Bar */}
        <Flex gap={3} mb={8}>
          <InputGroup maxW="450px">
            <InputLeftElement pointerEvents="none" pt={1}>
              <SearchIcon />
            </InputLeftElement>
            <Input
              placeholder="Search prompts, categories, or models..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              bg="#0F1A11"
              color="#F4F7F0"
              border="1px solid #2A3A2C"
              borderRadius="10px"
              pl={10}
              _placeholder={{ color: '#6B7B6D' }}
              _focus={{ borderColor: '#B7FF35' }}
            />
          </InputGroup>
        </Flex>

        {/* Image Grid */}
        {filteredImages.length > 0 ? (
          <Grid templateColumns="repeat(auto-fill, minmax(280px, 1fr))" gap={5} mb={8}>
            {filteredImages.map((img) => (
              <GridItem key={img.id}>
                <Box
                  bg="#111713"
                  borderRadius="14px"
                  border="1px solid #2A3A2C"
                  overflow="hidden"
                  transition="all 0.25s ease"
                  _hover={{
                    borderColor: '#B7FF35',
                    transform: 'translateY(-3px)',
                    boxShadow: '0 12px 40px rgba(0,0,0,0.6)',
                  }}
                  cursor="pointer"
                  onClick={() => setInspectImage(img)}
                  onMouseEnter={() => setHoveredCard(img.id)}
                  onMouseLeave={() => setHoveredCard(null)}
                >
                  {/* Image Container */}
                  <Box position="relative" overflow="hidden">
                    <Box
                      as="img"
                      src={`https://picsum.photos/seed/${img.seed}/500/350`}
                      alt={img.prompt}
                      w="100%"
                      h="220px"
                      objectFit="cover"
                      transition="transform 0.4s ease"
                    />

                    {/* Category Tag */}
                    <Box position="absolute" top={2.5} left={2.5}>
                      <Badge bg="rgba(8,11,10,0.85)" color={img.category === 'Selective Inpaint' ? '#B7FF35' : '#F4F7F0'} fontSize="10px" px={2} py={0.5} borderRadius="4px">
                        {img.category}
                      </Badge>
                    </Box>

                    {/* Like button top right */}
                    <Box
                      position="absolute"
                      top={2.5}
                      right={2.5}
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleLike(img.id);
                      }}
                      p={1.5}
                      borderRadius="full"
                      bg="rgba(0,0,0,0.6)"
                      _hover={{ bg: 'rgba(0,0,0,0.85)' }}
                    >
                      <HeartIcon filled={likedImages.has(img.id)} />
                    </Box>
                  </Box>

                  {/* Card Content */}
                  <Box p={3.5}>
                    <Text color="#F4F7F0" fontSize="xs" fontWeight="500" noOfLines={2} mb={2}>
                      {img.prompt}
                    </Text>
                    <Flex justify="space-between" align="center" pt={2} borderTop="1px solid #1A2A1C">
                      <Text fontSize="10px" color="#6B7B6D">{img.model}</Text>
                      <Text fontSize="10px" color="#A5B1A7">{img.date}</Text>
                    </Flex>
                  </Box>
                </Box>
              </GridItem>
            ))}
          </Grid>
        ) : (
          <Box textAlign="center" py={16}>
            <Text fontSize="36px" mb={2}>🖼️</Text>
            <Text color="#A5B1A7" fontSize="sm">No creations found matching your filter</Text>
          </Box>
        )}

        {/* LIGHTBOX / IMAGE DETAIL INSPECTOR MODAL */}
        <Modal isOpen={!!inspectImage} onClose={() => setInspectImage(null)} isCentered size="xl">
          <ModalOverlay bg="rgba(0,0,0,0.88)" backdropFilter="blur(8px)" />
          <ModalContent bg="#111713" border="1px solid #2A3A2C" borderRadius="18px" color="#F4F7F0">
            <ModalHeader borderBottom="1px solid #1A2A1C" py={3.5}>
              <Flex align="center" justify="space-between">
                <Badge bg="rgba(183,255,53,0.15)" color="#B7FF35" fontSize="10px" px={2} py={0.5} borderRadius="4px">
                  {inspectImage?.category}
                </Badge>
                <ModalCloseButton position="static" color="#A5B1A7" />
              </Flex>
            </ModalHeader>

            <ModalBody py={4}>
              {inspectImage && (
                <>
                  <Box borderRadius="12px" overflow="hidden" border="1px solid #2A3A2C" mb={4} bg="#080B0A">
                    <Box
                      as="img"
                      src={`https://picsum.photos/seed/${inspectImage.seed}/800/500`}
                      alt={inspectImage.prompt}
                      w="100%"
                      maxH="380px"
                      objectFit="contain"
                    />
                  </Box>

                  <Text fontSize="10px" color="#6B7B6D" textTransform="uppercase" fontWeight="bold" mb={1}>
                    Generation Prompt
                  </Text>
                  <Text fontSize="sm" color="#F4F7F0" mb={3} lineHeight="1.6">
                    {inspectImage.prompt}
                  </Text>

                  <Flex justify="space-between" align="center" bg="#0D120E" p={2.5} borderRadius="8px" border="1px solid #1A2A1C">
                    <Text fontSize="xs" color="#A5B1A7">Model: <span style={{ color: '#F4F7F0' }}>{inspectImage.model}</span></Text>
                    <Text fontSize="xs" color="#A5B1A7">Created: <span style={{ color: '#F4F7F0' }}>{inspectImage.date}</span></Text>
                  </Flex>
                </>
              )}
            </ModalBody>

            <ModalFooter borderTop="1px solid #1A2A1C" py={3} justify="space-between">
              <HStack spacing={2}>
                <Button
                  size="sm"
                  bg="#B7FF35"
                  color="#080B0A"
                  fontWeight="bold"
                  leftIcon={<Text>🎨</Text>}
                  onClick={() => {
                    navigate('/create');
                    setInspectImage(null);
                  }}
                >
                  Remix in Generator
                </Button>
                {inspectImage && (
                  <Button
                    as="a"
                    href={`https://picsum.photos/seed/${inspectImage.seed}/800/500`}
                    download="creation.png"
                    target="_blank"
                    size="sm"
                    variant="outline"
                    borderColor="#2A3A2C"
                    color="#F4F7F0"
                    leftIcon={<DownloadIcon />}
                  >
                    Save
                  </Button>
                )}
              </HStack>

              <Button size="sm" variant="ghost" color="#A5B1A7" onClick={() => setInspectImage(null)}>
                Close
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </Box>
    </WorkspaceLayout>
  );
};

export default Gallery;
