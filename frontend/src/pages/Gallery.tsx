import React, { useState } from 'react';
import {
  Box, Flex, Text, Heading, Button, Input, Grid, GridItem,
  InputGroup, InputLeftElement,
} from '@chakra-ui/react';
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

const EditIcon: React.FC = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#F4F7F0" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
  </svg>
);

const FilterIcon: React.FC = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#A5B1A7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
  </svg>
);

interface ImageCard {
  id: number;
  seed: number;
  prompt: string;
  date: string;
  liked: boolean;
}

const IMAGES: ImageCard[] = [
  { id: 1, seed: 10, prompt: 'A serene mountain landscape at golden hour with mist', date: 'Nov 6, 2026', liked: false },
  { id: 2, seed: 22, prompt: 'Cyberpunk city street with neon reflections on wet pavement', date: 'Nov 6, 2026', liked: true },
  { id: 3, seed: 33, prompt: 'Portrait of a woman in Renaissance oil painting style', date: 'Nov 5, 2026', liked: false },
  { id: 4, seed: 44, prompt: 'Minimalist Japanese zen garden with raked sand patterns', date: 'Nov 5, 2026', liked: true },
  { id: 5, seed: 55, prompt: 'Abstract geometric art with bold primary colors', date: 'Nov 4, 2026', liked: false },
  { id: 6, seed: 66, prompt: 'Underwater coral reef teeming with tropical fish', date: 'Nov 4, 2026', liked: false },
  { id: 7, seed: 77, prompt: 'Steampunk mechanical owl perched on a brass clock tower', date: 'Nov 3, 2026', liked: true },
  { id: 8, seed: 88, prompt: 'Northern lights aurora over a frozen lake in Iceland', date: 'Nov 3, 2026', liked: false },
  { id: 9, seed: 99, prompt: 'Photorealistic macro shot of dewdrops on a spider web', date: 'Nov 2, 2026', liked: false },
  { id: 10, seed: 111, prompt: 'Fantasy castle floating among clouds at sunset', date: 'Nov 2, 2026', liked: true },
  { id: 11, seed: 123, prompt: 'Vintage film noir detective in a rainy alley', date: 'Nov 1, 2026', liked: false },
  { id: 12, seed: 135, prompt: 'Isometric pixel art of a cozy coffee shop interior', date: 'Nov 1, 2026', liked: false },
];

const TABS = ['All', 'Created', 'Liked', 'Favorites', 'Collections'];

const Gallery: React.FC = () => {
  const [activeTab, setActiveTab] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [likedImages, setLikedImages] = useState<Set<number>>(
    new Set(IMAGES.filter((img) => img.liked).map((img) => img.id))
  );
  const [currentPage, setCurrentPage] = useState(1);
  const [hoveredCard, setHoveredCard] = useState<number | null>(null);

  const toggleLike = (id: number) => {
    setLikedImages((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const filteredImages = IMAGES.filter((img) => {
    if (activeTab === 'Liked' && !likedImages.has(img.id)) return false;
    if (activeTab === 'Favorites' && !likedImages.has(img.id)) return false;
    if (searchQuery && !img.prompt.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  return (
    <WorkspaceLayout>
      <Box p={8} minH="100vh" bg="#080B0A">
        {/* Header */}
        <Flex align="center" justify="space-between" mb={6}>
          <Box>
            <Heading size="lg" color="#F4F7F0" fontWeight={700}>
              Gallery
            </Heading>
            <Text color="#A5B1A7" mt={1} fontSize="sm">
              Browse, manage, and organize your generated images
            </Text>
          </Box>
          <Flex gap={3}>
            <Text color="#A5B1A7" fontSize="sm" alignSelf="center">
              {filteredImages.length} images
            </Text>
          </Flex>
        </Flex>

        {/* Tabs */}
        <Flex gap={2} mb={5} flexWrap="wrap">
          {TABS.map((tab) => (
            <Button
              key={tab}
              onClick={() => setActiveTab(tab)}
              bg={activeTab === tab ? '#B7FF35' : '#111713'}
              color={activeTab === tab ? '#080B0A' : '#A5B1A7'}
              border="1px solid"
              borderColor={activeTab === tab ? '#B7FF35' : '#2A3A2C'}
              borderRadius="full"
              px={5}
              py={1}
              size="sm"
              fontWeight={600}
              _hover={{
                bg: activeTab === tab ? '#8DDB39' : '#1A2A1C',
                color: activeTab === tab ? '#080B0A' : '#F4F7F0',
              }}
              transition="all 0.2s ease"
            >
              {tab}
            </Button>
          ))}
        </Flex>

        {/* Search & Filters */}
        <Flex gap={3} mb={7}>
          <InputGroup flex={1} maxW="480px">
            <InputLeftElement pointerEvents="none" h="full" pl={3}>
              <SearchIcon />
            </InputLeftElement>
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by prompt, style, or keyword..."
              bg="#0F1A11"
              color="#F4F7F0"
              border="1px solid #2A3A2C"
              borderRadius="10px"
              pl={10}
              _placeholder={{ color: '#A5B1A7' }}
              _hover={{ borderColor: '#B7FF35' }}
              _focus={{ borderColor: '#B7FF35', boxShadow: '0 0 0 1px #B7FF35' }}
            />
          </InputGroup>
          <Button
            bg="#111713"
            color="#A5B1A7"
            border="1px solid #2A3A2C"
            borderRadius="10px"
            _hover={{ bg: '#1A2A1C', color: '#F4F7F0' }}
            leftIcon={<FilterIcon />}
          >
            Filters
          </Button>
          <Button
            bg="#111713"
            color="#A5B1A7"
            border="1px solid #2A3A2C"
            borderRadius="10px"
            _hover={{ bg: '#1A2A1C', color: '#F4F7F0' }}
          >
            Sort: Newest
          </Button>
        </Flex>

        {/* Image Grid */}
        {filteredImages.length > 0 ? (
          <Grid templateColumns="repeat(auto-fill, minmax(260px, 1fr))" gap={5} mb={8}>
            {filteredImages.map((img) => (
              <GridItem key={img.id}>
                <Box
                  bg="#111713"
                  borderRadius="14px"
                  border="1px solid #2A3A2C"
                  overflow="hidden"
                  transition="all 0.3s ease"
                  _hover={{
                    borderColor: '#B7FF35',
                    transform: 'translateY(-4px)',
                    boxShadow: '0 12px 40px rgba(183,255,53,0.08)',
                  }}
                  cursor="pointer"
                  onMouseEnter={() => setHoveredCard(img.id)}
                  onMouseLeave={() => setHoveredCard(null)}
                >
                  {/* Image Container */}
                  <Box position="relative" overflow="hidden">
                    <Box
                      as="img"
                      src={`https://picsum.photos/seed/${img.seed}/400/400`}
                      alt={img.prompt}
                      w="100%"
                      h="260px"
                      objectFit="cover"
                      transition="transform 0.4s ease"
                      sx={hoveredCard === img.id ? { transform: 'scale(1.05)' } : {}}
                    />

                    {/* Hover Overlay */}
                    <Box
                      position="absolute"
                      top={0}
                      left={0}
                      right={0}
                      bottom={0}
                      bg="rgba(8,11,10,0.65)"
                      opacity={hoveredCard === img.id ? 1 : 0}
                      transition="opacity 0.3s ease"
                      display="flex"
                      alignItems="center"
                      justifyContent="center"
                    >
                      <Flex gap={3}>
                        <Box
                          as="button"
                          onClick={(e: React.MouseEvent) => { e.stopPropagation(); toggleLike(img.id); }}
                          w="42px"
                          h="42px"
                          borderRadius="10px"
                          bg="rgba(255,255,255,0.1)"
                          display="flex"
                          alignItems="center"
                          justifyContent="center"
                          cursor="pointer"
                          _hover={{ bg: 'rgba(255,255,255,0.2)' }}
                          transition="all 0.2s"
                          backdropFilter="blur(8px)"
                        >
                          <HeartIcon filled={likedImages.has(img.id)} />
                        </Box>
                        <Box
                          as="button"
                          w="42px"
                          h="42px"
                          borderRadius="10px"
                          bg="rgba(255,255,255,0.1)"
                          display="flex"
                          alignItems="center"
                          justifyContent="center"
                          cursor="pointer"
                          _hover={{ bg: 'rgba(255,255,255,0.2)' }}
                          transition="all 0.2s"
                          backdropFilter="blur(8px)"
                        >
                          <DownloadIcon />
                        </Box>
                        <Box
                          as="button"
                          w="42px"
                          h="42px"
                          borderRadius="10px"
                          bg="rgba(255,255,255,0.1)"
                          display="flex"
                          alignItems="center"
                          justifyContent="center"
                          cursor="pointer"
                          _hover={{ bg: 'rgba(255,255,255,0.2)' }}
                          transition="all 0.2s"
                          backdropFilter="blur(8px)"
                        >
                          <EditIcon />
                        </Box>
                      </Flex>
                    </Box>

                    {/* Liked Badge */}
                    {likedImages.has(img.id) && hoveredCard !== img.id && (
                      <Box position="absolute" top={3} right={3}>
                        <HeartIcon filled />
                      </Box>
                    )}
                  </Box>

                  {/* Metadata */}
                  <Box p={3}>
                    <Text color="#F4F7F0" fontSize="sm" noOfLines={1} fontWeight={500}>
                      {img.prompt}
                    </Text>
                    <Text color="#A5B1A7" fontSize="xs" mt={1}>
                      {img.date}
                    </Text>
                  </Box>
                </Box>
              </GridItem>
            ))}
          </Grid>
        ) : (
          <Flex
            direction="column"
            align="center"
            justify="center"
            minH="300px"
            bg="#111713"
            borderRadius="16px"
            border="1px solid #2A3A2C"
          >
            <Text color="#A5B1A7" fontSize="lg" mb={2}>
              No images found
            </Text>
            <Text color="#A5B1A7" fontSize="sm">
              Try adjusting your search or filters
            </Text>
          </Flex>
        )}

        {/* Pagination */}
        {filteredImages.length > 0 && (
          <Flex justify="center" align="center" gap={1} mt={4}>
            <Button
              size="sm"
              bg="transparent"
              color="#A5B1A7"
              _hover={{ bg: '#1A2A1C', color: '#F4F7F0' }}
              borderRadius="8px"
              isDisabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            >
              ← Prev
            </Button>
            {[1, 2, 3].map((p) => (
              <Button
                key={p}
                size="sm"
                w="36px"
                h="36px"
                bg={currentPage === p ? '#B7FF35' : 'transparent'}
                color={currentPage === p ? '#080B0A' : '#A5B1A7'}
                fontWeight={currentPage === p ? 700 : 500}
                borderRadius="8px"
                _hover={{
                  bg: currentPage === p ? '#8DDB39' : '#1A2A1C',
                  color: currentPage === p ? '#080B0A' : '#F4F7F0',
                }}
                onClick={() => setCurrentPage(p)}
              >
                {p}
              </Button>
            ))}
            <Text color="#A5B1A7" fontSize="sm" px={1}>...</Text>
            <Button
              size="sm"
              w="36px"
              h="36px"
              bg="transparent"
              color="#A5B1A7"
              borderRadius="8px"
              _hover={{ bg: '#1A2A1C', color: '#F4F7F0' }}
              onClick={() => setCurrentPage(10)}
            >
              10
            </Button>
            <Button
              size="sm"
              bg="transparent"
              color="#A5B1A7"
              _hover={{ bg: '#1A2A1C', color: '#F4F7F0' }}
              borderRadius="8px"
              onClick={() => setCurrentPage((p) => p + 1)}
            >
              Next →
            </Button>
          </Flex>
        )}
      </Box>
    </WorkspaceLayout>
  );
};

export default Gallery;
