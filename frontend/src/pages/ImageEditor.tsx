import React, { useState } from 'react';
import {
  Box,
  Flex,
  Text,
  Heading,
  Button,
  IconButton,
  Image,
  Select,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  Badge,
  VStack,
  HStack,
  Divider,
  Tooltip,
  Grid,
} from '@chakra-ui/react';
import {
  FiUpload,
  FiDownload,
  FiSave,
  FiImage,
  FiDroplet,
  FiSun,
  FiZap,
  FiScissors,
  FiTrash2,
  FiLayers,
  FiToggleLeft,
  FiToggleRight,
  FiMaximize,
  FiGrid,
} from 'react-icons/fi';
import WorkspaceLayout from '../components/WorkspaceLayout';

const ImageEditor: React.FC = () => {
  const [brightness, setBrightness] = useState(50);
  const [contrast, setContrast] = useState(50);
  const [saturation, setSaturation] = useState(50);
  const [showBefore, setShowBefore] = useState(false);
  const [hasImage, setHasImage] = useState(true);
  const [selectedStyle, setSelectedStyle] = useState('');

  return (
    <WorkspaceLayout>
      <Box p={6} minH="100vh" bg="#080B0A">
        {/* Header */}
        <Flex align="center" justify="space-between" mb={6}>
          <Flex align="center" gap={3}>
            <Heading size="lg" color="#F4F7F0" fontWeight="700">
              Image Editor
            </Heading>
            <Badge
              bg="rgba(183, 255, 53, 0.15)"
              color="#B7FF35"
              px={3}
              py={1}
              borderRadius="full"
              fontSize="xs"
              fontWeight="600"
              textTransform="none"
            >
              AI Edit
            </Badge>
          </Flex>
          <HStack spacing={3}>
            <Button
              size="sm"
              variant="outline"
              borderColor="#2A3A2C"
              color="#A5B1A7"
              _hover={{ bg: '#1A2A1C', borderColor: '#B7FF35', color: '#F4F7F0' }}
              leftIcon={<FiGrid />}
            >
              Grid View
            </Button>
            <Button
              size="sm"
              variant="outline"
              borderColor="#2A3A2C"
              color="#A5B1A7"
              _hover={{ bg: '#1A2A1C', borderColor: '#B7FF35', color: '#F4F7F0' }}
              leftIcon={<FiMaximize />}
            >
              Fullscreen
            </Button>
          </HStack>
        </Flex>

        {/* Main Layout */}
        <Flex gap={5} h="calc(100vh - 140px)">
          {/* Left: Image Preview Area */}
          <Box flex={1} display="flex" flexDir="column" gap={4}>
            {/* Upload Zone */}
            <Box
              bg="#111713"
              border="2px dashed #2A3A2C"
              borderRadius="xl"
              p={4}
              textAlign="center"
              cursor="pointer"
              _hover={{ borderColor: '#B7FF35', bg: '#182019' }}
              transition="all 0.2s ease"
              onClick={() => setHasImage(true)}
            >
              <Flex align="center" justify="center" gap={3}>
                <FiUpload color="#A5B1A7" size={18} />
                <Text color="#A5B1A7" fontSize="sm">
                  Upload or select an image — drag & drop or click to browse
                </Text>
              </Flex>
            </Box>

            {/* Image Preview */}
            <Box
              flex={1}
              bg="#111713"
              borderRadius="xl"
              border="1px solid #2A3A2C"
              overflow="hidden"
              position="relative"
              display="flex"
              alignItems="center"
              justifyContent="center"
            >
              {hasImage ? (
                <>
                  <Image
                    src={
                      showBefore
                        ? 'https://picsum.photos/seed/editor-before/900/600'
                        : 'https://picsum.photos/seed/editor-after/900/600'
                    }
                    alt="Editing preview"
                    objectFit="contain"
                    maxH="100%"
                    maxW="100%"
                    filter={`brightness(${brightness / 50}) contrast(${contrast / 50}) saturate(${saturation / 50})`}
                    transition="filter 0.3s ease"
                  />
                  {/* Before/After Toggle */}
                  <Flex
                    position="absolute"
                    bottom={4}
                    left="50%"
                    transform="translateX(-50%)"
                    bg="rgba(17, 23, 19, 0.9)"
                    borderRadius="full"
                    border="1px solid #2A3A2C"
                    p={1}
                    gap={1}
                    backdropFilter="blur(10px)"
                  >
                    <Button
                      size="sm"
                      bg={!showBefore ? '#B7FF35' : 'transparent'}
                      color={!showBefore ? '#080B0A' : '#A5B1A7'}
                      borderRadius="full"
                      px={4}
                      fontSize="xs"
                      fontWeight="600"
                      _hover={{ bg: !showBefore ? '#B7FF35' : '#1A2A1C' }}
                      onClick={() => setShowBefore(false)}
                    >
                      After
                    </Button>
                    <Button
                      size="sm"
                      bg={showBefore ? '#B7FF35' : 'transparent'}
                      color={showBefore ? '#080B0A' : '#A5B1A7'}
                      borderRadius="full"
                      px={4}
                      fontSize="xs"
                      fontWeight="600"
                      _hover={{ bg: showBefore ? '#B7FF35' : '#1A2A1C' }}
                      onClick={() => setShowBefore(true)}
                    >
                      Before
                    </Button>
                  </Flex>

                  {/* Image Info */}
                  <Flex
                    position="absolute"
                    top={4}
                    left={4}
                    bg="rgba(17, 23, 19, 0.85)"
                    borderRadius="lg"
                    px={3}
                    py={1.5}
                    gap={3}
                    backdropFilter="blur(10px)"
                    border="1px solid #2A3A2C"
                  >
                    <Text color="#A5B1A7" fontSize="xs">1920 × 1280</Text>
                    <Text color="#2A3A2C">|</Text>
                    <Text color="#A5B1A7" fontSize="xs">2.4 MB</Text>
                    <Text color="#2A3A2C">|</Text>
                    <Text color="#A5B1A7" fontSize="xs">PNG</Text>
                  </Flex>
                </>
              ) : (
                <VStack spacing={3}>
                  <FiImage color="#2A3A2C" size={64} />
                  <Text color="#A5B1A7" fontSize="sm">
                    No image loaded
                  </Text>
                </VStack>
              )}
            </Box>
          </Box>

          {/* Right: Edit Controls Panel */}
          <Box
            w="340px"
            minW="340px"
            bg="#111713"
            borderRadius="xl"
            border="1px solid #2A3A2C"
            p={5}
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
              {/* AI Tools */}
              <Box>
                <Text
                  color="#A5B1A7"
                  fontSize="xs"
                  fontWeight="600"
                  textTransform="uppercase"
                  letterSpacing="wider"
                  mb={3}
                >
                  AI Tools
                </Text>
                <Grid templateColumns="1fr 1fr" gap={2}>
                  <Button
                    size="sm"
                    bg="#182019"
                    color="#F4F7F0"
                    border="1px solid #2A3A2C"
                    borderRadius="lg"
                    leftIcon={<FiDroplet size={14} />}
                    _hover={{ bg: '#1A2A1C', borderColor: '#B7FF35' }}
                    transition="all 0.2s"
                    fontWeight="500"
                    fontSize="xs"
                  >
                    Inpaint
                  </Button>
                  <Button
                    size="sm"
                    bg="#182019"
                    color="#F4F7F0"
                    border="1px solid #2A3A2C"
                    borderRadius="lg"
                    leftIcon={<FiMaximize size={14} />}
                    _hover={{ bg: '#1A2A1C', borderColor: '#B7FF35' }}
                    transition="all 0.2s"
                    fontWeight="500"
                    fontSize="xs"
                  >
                    Outpaint
                  </Button>
                  <Button
                    size="sm"
                    bg="#182019"
                    color="#F4F7F0"
                    border="1px solid #2A3A2C"
                    borderRadius="lg"
                    leftIcon={<FiScissors size={14} />}
                    _hover={{ bg: '#1A2A1C', borderColor: '#B7FF35' }}
                    transition="all 0.2s"
                    fontWeight="500"
                    fontSize="xs"
                  >
                    Remove Object
                  </Button>
                  <Button
                    size="sm"
                    bg="#182019"
                    color="#F4F7F0"
                    border="1px solid #2A3A2C"
                    borderRadius="lg"
                    leftIcon={<FiTrash2 size={14} />}
                    _hover={{ bg: '#1A2A1C', borderColor: '#B7FF35' }}
                    transition="all 0.2s"
                    fontWeight="500"
                    fontSize="xs"
                  >
                    Remove BG
                  </Button>
                </Grid>
              </Box>

              <Divider borderColor="#2A3A2C" />

              {/* Style */}
              <Box>
                <Text
                  color="#A5B1A7"
                  fontSize="xs"
                  fontWeight="600"
                  textTransform="uppercase"
                  letterSpacing="wider"
                  mb={3}
                >
                  Change Style
                </Text>
                <Select
                  size="sm"
                  bg="#0F1A11"
                  border="1px solid #2A3A2C"
                  borderRadius="lg"
                  color="#F4F7F0"
                  _hover={{ borderColor: '#B7FF35' }}
                  _focus={{ borderColor: '#B7FF35', boxShadow: '0 0 0 1px #B7FF35' }}
                  value={selectedStyle}
                  onChange={(e) => setSelectedStyle(e.target.value)}
                >
                  <option value="" style={{ background: '#111713' }}>
                    Select a style...
                  </option>
                  <option value="realistic" style={{ background: '#111713' }}>
                    Photorealistic
                  </option>
                  <option value="anime" style={{ background: '#111713' }}>
                    Anime / Manga
                  </option>
                  <option value="oil" style={{ background: '#111713' }}>
                    Oil Painting
                  </option>
                  <option value="watercolor" style={{ background: '#111713' }}>
                    Watercolor
                  </option>
                  <option value="sketch" style={{ background: '#111713' }}>
                    Pencil Sketch
                  </option>
                  <option value="cyberpunk" style={{ background: '#111713' }}>
                    Cyberpunk
                  </option>
                  <option value="fantasy" style={{ background: '#111713' }}>
                    Fantasy Art
                  </option>
                </Select>
              </Box>

              <Divider borderColor="#2A3A2C" />

              {/* Adjustments */}
              <Box>
                <Text
                  color="#A5B1A7"
                  fontSize="xs"
                  fontWeight="600"
                  textTransform="uppercase"
                  letterSpacing="wider"
                  mb={4}
                >
                  Adjustments
                </Text>
                <VStack spacing={5} align="stretch">
                  {/* Brightness */}
                  <Box>
                    <Flex justify="space-between" mb={2}>
                      <Flex align="center" gap={2}>
                        <FiSun size={13} color="#A5B1A7" />
                        <Text color="#F4F7F0" fontSize="xs" fontWeight="500">
                          Brightness
                        </Text>
                      </Flex>
                      <Text color="#B7FF35" fontSize="xs" fontWeight="600">
                        {brightness}%
                      </Text>
                    </Flex>
                    <Slider
                      value={brightness}
                      onChange={setBrightness}
                      min={0}
                      max={100}
                    >
                      <SliderTrack bg="#0F1A11" h="6px" borderRadius="full">
                        <SliderFilledTrack bg="#B7FF35" borderRadius="full" />
                      </SliderTrack>
                      <SliderThumb
                        boxSize={4}
                        bg="#B7FF35"
                        border="2px solid #080B0A"
                        _focus={{ boxShadow: '0 0 0 3px rgba(183,255,53,0.3)' }}
                      />
                    </Slider>
                  </Box>

                  {/* Contrast */}
                  <Box>
                    <Flex justify="space-between" mb={2}>
                      <Flex align="center" gap={2}>
                        <FiZap size={13} color="#A5B1A7" />
                        <Text color="#F4F7F0" fontSize="xs" fontWeight="500">
                          Contrast
                        </Text>
                      </Flex>
                      <Text color="#B7FF35" fontSize="xs" fontWeight="600">
                        {contrast}%
                      </Text>
                    </Flex>
                    <Slider
                      value={contrast}
                      onChange={setContrast}
                      min={0}
                      max={100}
                    >
                      <SliderTrack bg="#0F1A11" h="6px" borderRadius="full">
                        <SliderFilledTrack bg="#8DDB39" borderRadius="full" />
                      </SliderTrack>
                      <SliderThumb
                        boxSize={4}
                        bg="#8DDB39"
                        border="2px solid #080B0A"
                        _focus={{ boxShadow: '0 0 0 3px rgba(141,219,57,0.3)' }}
                      />
                    </Slider>
                  </Box>

                  {/* Saturation */}
                  <Box>
                    <Flex justify="space-between" mb={2}>
                      <Flex align="center" gap={2}>
                        <FiDroplet size={13} color="#A5B1A7" />
                        <Text color="#F4F7F0" fontSize="xs" fontWeight="500">
                          Saturation
                        </Text>
                      </Flex>
                      <Text color="#B7FF35" fontSize="xs" fontWeight="600">
                        {saturation}%
                      </Text>
                    </Flex>
                    <Slider
                      value={saturation}
                      onChange={setSaturation}
                      min={0}
                      max={100}
                    >
                      <SliderTrack bg="#0F1A11" h="6px" borderRadius="full">
                        <SliderFilledTrack
                          bg="linear-gradient(90deg, #8DDB39, #B7FF35)"
                          borderRadius="full"
                        />
                      </SliderTrack>
                      <SliderThumb
                        boxSize={4}
                        bg="#B7FF35"
                        border="2px solid #080B0A"
                        _focus={{ boxShadow: '0 0 0 3px rgba(183,255,53,0.3)' }}
                      />
                    </Slider>
                  </Box>
                </VStack>
              </Box>

              <Divider borderColor="#2A3A2C" />

              {/* Apply */}
              <Button
                bg="#B7FF35"
                color="#080B0A"
                size="md"
                borderRadius="lg"
                fontWeight="700"
                _hover={{ bg: '#8DDB39', transform: 'translateY(-1px)' }}
                _active={{ transform: 'translateY(0)' }}
                transition="all 0.2s"
                boxShadow="0 0 20px rgba(183,255,53,0.2)"
              >
                ✨ Apply Changes
              </Button>

              <Divider borderColor="#2A3A2C" />

              {/* Save/Download */}
              <VStack spacing={2}>
                <Button
                  w="100%"
                  size="sm"
                  bg="#182019"
                  color="#F4F7F0"
                  border="1px solid #2A3A2C"
                  borderRadius="lg"
                  leftIcon={<FiSave size={14} />}
                  _hover={{ bg: '#1A2A1C', borderColor: '#B7FF35' }}
                  transition="all 0.2s"
                  fontWeight="500"
                >
                  Save to Gallery
                </Button>
                <Button
                  w="100%"
                  size="sm"
                  bg="#182019"
                  color="#F4F7F0"
                  border="1px solid #2A3A2C"
                  borderRadius="lg"
                  leftIcon={<FiDownload size={14} />}
                  _hover={{ bg: '#1A2A1C', borderColor: '#B7FF35' }}
                  transition="all 0.2s"
                  fontWeight="500"
                >
                  Download
                </Button>
              </VStack>
            </VStack>
          </Box>
        </Flex>
      </Box>
    </WorkspaceLayout>
  );
};

export default ImageEditor;
