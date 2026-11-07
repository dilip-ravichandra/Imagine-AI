import React, { useState } from 'react';
import {
  Box,
  Flex,
  Text,
  Heading,
  Button,
  IconButton,
  Image,
  VStack,
  HStack,
  Divider,
  Tooltip,
  Switch,
} from '@chakra-ui/react';
import {
  FiMousePointer,
  FiType,
  FiImage,
  FiEdit2,
  FiCircle,
  FiSquare,
  FiMinus,
  FiPlus,
  FiMaximize,
  FiSave,
  FiDownload,
  FiEye,
  FiEyeOff,
  FiTrash2,
  FiLayers,
  FiMove,
  FiZoomIn,
} from 'react-icons/fi';
import WorkspaceLayout from '../components/WorkspaceLayout';

interface LayerItem {
  id: number;
  name: string;
  type: 'text' | 'image' | 'shape';
  visible: boolean;
}

const ImagineCanvas: React.FC = () => {
  const [zoom, setZoom] = useState(100);
  const [activeTool, setActiveTool] = useState('select');
  const [layers, setLayers] = useState<LayerItem[]>([
    { id: 1, name: 'Eco City Concept', type: 'text', visible: true },
    { id: 2, name: 'Reference Photo', type: 'image', visible: true },
    { id: 3, name: 'Smart Building Label', type: 'text', visible: true },
    { id: 4, name: 'Design Grid', type: 'shape', visible: true },
  ]);

  const toggleLayerVisibility = (id: number) => {
    setLayers((prev) =>
      prev.map((l) => (l.id === id ? { ...l, visible: !l.visible } : l))
    );
  };

  const tools = [
    { id: 'select', icon: FiMousePointer, label: 'Select' },
    { id: 'move', icon: FiMove, label: 'Move' },
    { id: 'text', icon: FiType, label: 'Text' },
    { id: 'image', icon: FiImage, label: 'Image' },
    { id: 'draw', icon: FiEdit2, label: 'Draw' },
    { id: 'eraser', icon: FiTrash2, label: 'Eraser' },
    { id: 'circle', icon: FiCircle, label: 'Circle' },
    { id: 'rect', icon: FiSquare, label: 'Rectangle' },
  ];

  const getLayerIcon = (type: string) => {
    switch (type) {
      case 'text':
        return <FiType size={12} />;
      case 'image':
        return <FiImage size={12} />;
      case 'shape':
        return <FiSquare size={12} />;
      default:
        return <FiLayers size={12} />;
    }
  };

  return (
    <WorkspaceLayout>
      <Box p={0} minH="100vh" bg="#080B0A" display="flex" flexDir="column">
        {/* Top Header Bar */}
        <Flex
          align="center"
          justify="space-between"
          px={5}
          py={3}
          borderBottom="1px solid #2A3A2C"
          bg="#0D120E"
        >
          <Flex align="center" gap={3}>
            <Heading size="md" color="#F4F7F0" fontWeight="700">
              Imagine Canvas
            </Heading>
            <Box
              bg="rgba(183, 255, 53, 0.1)"
              px={2}
              py={0.5}
              borderRadius="md"
            >
              <Text color="#B7FF35" fontSize="xs" fontWeight="600">
                Untitled Project
              </Text>
            </Box>
          </Flex>

          {/* Zoom Controls */}
          <HStack
            spacing={1}
            bg="#111713"
            border="1px solid #2A3A2C"
            borderRadius="lg"
            px={2}
            py={1}
          >
            <IconButton
              aria-label="Zoom out"
              icon={<FiMinus size={14} />}
              size="xs"
              variant="ghost"
              color="#A5B1A7"
              _hover={{ bg: '#1A2A1C', color: '#F4F7F0' }}
              onClick={() => setZoom(Math.max(25, zoom - 10))}
            />
            <Box
              px={3}
              py={1}
              minW="60px"
              textAlign="center"
              bg="#0F1A11"
              borderRadius="md"
            >
              <Text color="#B7FF35" fontSize="xs" fontWeight="700">
                {zoom}%
              </Text>
            </Box>
            <IconButton
              aria-label="Zoom in"
              icon={<FiPlus size={14} />}
              size="xs"
              variant="ghost"
              color="#A5B1A7"
              _hover={{ bg: '#1A2A1C', color: '#F4F7F0' }}
              onClick={() => setZoom(Math.min(400, zoom + 10))}
            />
            <Divider
              orientation="vertical"
              h="20px"
              borderColor="#2A3A2C"
            />
            <IconButton
              aria-label="Fit to screen"
              icon={<FiMaximize size={14} />}
              size="xs"
              variant="ghost"
              color="#A5B1A7"
              _hover={{ bg: '#1A2A1C', color: '#F4F7F0' }}
              onClick={() => setZoom(100)}
            />
          </HStack>

          {/* Save / Export */}
          <HStack spacing={2}>
            <Button
              size="sm"
              bg="#182019"
              color="#F4F7F0"
              border="1px solid #2A3A2C"
              borderRadius="lg"
              leftIcon={<FiSave size={14} />}
              _hover={{ bg: '#1A2A1C', borderColor: '#B7FF35' }}
              transition="all 0.2s"
              fontWeight="500"
              fontSize="xs"
            >
              Save Project
            </Button>
            <Button
              size="sm"
              bg="#B7FF35"
              color="#080B0A"
              borderRadius="lg"
              leftIcon={<FiDownload size={14} />}
              _hover={{ bg: '#8DDB39' }}
              transition="all 0.2s"
              fontWeight="600"
              fontSize="xs"
            >
              Export
            </Button>
          </HStack>
        </Flex>

        {/* Main Area */}
        <Flex flex={1} overflow="hidden">
          {/* Left Toolbar */}
          <Flex
            direction="column"
            align="center"
            bg="#0D120E"
            borderRight="1px solid #2A3A2C"
            py={4}
            px={2}
            gap={1}
            w="56px"
            minW="56px"
          >
            {tools.map((tool) => (
              <Tooltip
                key={tool.id}
                label={tool.label}
                placement="right"
                bg="#182019"
                color="#F4F7F0"
                fontSize="xs"
                borderRadius="md"
              >
                <IconButton
                  aria-label={tool.label}
                  icon={<tool.icon size={18} />}
                  size="sm"
                  variant="ghost"
                  color={activeTool === tool.id ? '#B7FF35' : '#A5B1A7'}
                  bg={activeTool === tool.id ? 'rgba(183,255,53,0.1)' : 'transparent'}
                  borderRadius="lg"
                  w="40px"
                  h="40px"
                  _hover={{
                    bg: activeTool === tool.id
                      ? 'rgba(183,255,53,0.15)'
                      : '#1A2A1C',
                    color: '#F4F7F0',
                  }}
                  onClick={() => setActiveTool(tool.id)}
                  transition="all 0.15s"
                />
              </Tooltip>
            ))}
          </Flex>

          {/* Canvas Area */}
          <Box
            flex={1}
            bg="#0F1A11"
            position="relative"
            overflow="hidden"
            backgroundImage={`
              linear-gradient(rgba(42,58,44,0.3) 1px, transparent 1px),
              linear-gradient(90deg, rgba(42,58,44,0.3) 1px, transparent 1px)
            `}
            backgroundSize={`${20 * (zoom / 100)}px ${20 * (zoom / 100)}px`}
          >
            {/* Canvas Objects */}
            <Box
              position="absolute"
              top="0"
              left="0"
              w="100%"
              h="100%"
              transform={`scale(${zoom / 100})`}
              transformOrigin="center center"
              transition="transform 0.2s ease"
            >
              {/* Note Card 1: Eco City Concept */}
              {layers[0]?.visible && (
                <Box
                  position="absolute"
                  top="120px"
                  left="180px"
                  bg="#111713"
                  border="1px solid #2A3A2C"
                  borderRadius="xl"
                  p={5}
                  minW="260px"
                  boxShadow="0 8px 32px rgba(0,0,0,0.4)"
                  cursor="move"
                  _hover={{
                    borderColor: '#B7FF35',
                    boxShadow: '0 8px 32px rgba(183,255,53,0.1)',
                  }}
                  transition="all 0.2s"
                >
                  <Flex align="center" gap={2} mb={2}>
                    <Box w={3} h={3} bg="#B7FF35" borderRadius="full" />
                    <Text color="#B7FF35" fontSize="xs" fontWeight="600">
                      CONCEPT
                    </Text>
                  </Flex>
                  <Text color="#F4F7F0" fontSize="md" fontWeight="700" mb={2}>
                    My Idea: Eco City
                  </Text>
                  <Text color="#A5B1A7" fontSize="xs" lineHeight="1.6">
                    A self-sustaining urban environment powered by renewable
                    energy and vertical farms. Every building is a living
                    ecosystem.
                  </Text>
                  <Flex mt={3} gap={2}>
                    <Box
                      bg="rgba(183,255,53,0.1)"
                      px={2}
                      py={0.5}
                      borderRadius="full"
                    >
                      <Text color="#B7FF35" fontSize="10px" fontWeight="600">
                        Sustainability
                      </Text>
                    </Box>
                    <Box
                      bg="rgba(141,219,57,0.1)"
                      px={2}
                      py={0.5}
                      borderRadius="full"
                    >
                      <Text color="#8DDB39" fontSize="10px" fontWeight="600">
                        Architecture
                      </Text>
                    </Box>
                  </Flex>
                </Box>
              )}

              {/* Image Thumbnail */}
              {layers[1]?.visible && (
                <Box
                  position="absolute"
                  top="100px"
                  left="520px"
                  bg="#111713"
                  border="1px solid #2A3A2C"
                  borderRadius="xl"
                  overflow="hidden"
                  cursor="move"
                  boxShadow="0 8px 32px rgba(0,0,0,0.4)"
                  _hover={{
                    borderColor: '#B7FF35',
                    boxShadow: '0 8px 32px rgba(183,255,53,0.1)',
                  }}
                  transition="all 0.2s"
                >
                  <Image
                    src="https://picsum.photos/seed/canvas-ref/280/180"
                    alt="Reference"
                    w="280px"
                    h="180px"
                    objectFit="cover"
                  />
                  <Box px={3} py={2}>
                    <Text color="#F4F7F0" fontSize="xs" fontWeight="600">
                      Reference: Green Architecture
                    </Text>
                    <Text color="#A5B1A7" fontSize="10px" mt={0.5}>
                      Imported from gallery
                    </Text>
                  </Box>
                </Box>
              )}

              {/* Smart Building Label */}
              {layers[2]?.visible && (
                <Box
                  position="absolute"
                  top="340px"
                  left="340px"
                  bg="#111713"
                  border="1px solid #B7FF35"
                  borderRadius="lg"
                  px={4}
                  py={3}
                  cursor="move"
                  boxShadow="0 0 20px rgba(183,255,53,0.1)"
                  _hover={{
                    boxShadow: '0 0 30px rgba(183,255,53,0.2)',
                  }}
                  transition="all 0.2s"
                >
                  <Flex align="center" gap={2}>
                    <Box
                      w={2}
                      h={2}
                      bg="#B7FF35"
                      borderRadius="full"
                      boxShadow="0 0 6px #B7FF35"
                    />
                    <Text
                      color="#F4F7F0"
                      fontSize="sm"
                      fontWeight="700"
                      letterSpacing="wide"
                    >
                      Smart Building
                    </Text>
                  </Flex>
                  <Text color="#A5B1A7" fontSize="xs" mt={1}>
                    IoT-enabled, zero-emission residential complex
                  </Text>
                </Box>
              )}

              {/* Connection line visual hint */}
              {layers[3]?.visible && (
                <Box
                  position="absolute"
                  top="280px"
                  left="310px"
                  w="180px"
                  h="2px"
                  bg="linear-gradient(90deg, #B7FF35, transparent)"
                  opacity={0.3}
                  transform="rotate(25deg)"
                />
              )}
            </Box>

            {/* Canvas Hint */}
            <Flex
              position="absolute"
              bottom={4}
              left="50%"
              transform="translateX(-50%)"
              bg="rgba(17, 23, 19, 0.85)"
              borderRadius="full"
              px={4}
              py={2}
              gap={4}
              backdropFilter="blur(10px)"
              border="1px solid #2A3A2C"
            >
              <Text color="#A5B1A7" fontSize="10px">
                Scroll to pan • Ctrl+Scroll to zoom • Click objects to select
              </Text>
            </Flex>
          </Box>

          {/* Right Panel: Layers */}
          <Box
            w="240px"
            minW="240px"
            bg="#0D120E"
            borderLeft="1px solid #2A3A2C"
            p={0}
          >
            <Flex
              align="center"
              justify="space-between"
              px={4}
              py={3}
              borderBottom="1px solid #2A3A2C"
            >
              <Flex align="center" gap={2}>
                <FiLayers size={14} color="#B7FF35" />
                <Text color="#F4F7F0" fontSize="sm" fontWeight="600">
                  Layers
                </Text>
              </Flex>
              <Text color="#A5B1A7" fontSize="xs">
                {layers.length}
              </Text>
            </Flex>

            <VStack spacing={0} align="stretch">
              {layers.map((layer, idx) => (
                <Flex
                  key={layer.id}
                  align="center"
                  px={4}
                  py={3}
                  gap={3}
                  bg={idx === 0 ? 'rgba(183,255,53,0.05)' : 'transparent'}
                  borderBottom="1px solid #2A3A2C"
                  borderLeft={idx === 0 ? '2px solid #B7FF35' : '2px solid transparent'}
                  _hover={{ bg: '#1A2A1C' }}
                  cursor="pointer"
                  transition="all 0.15s"
                >
                  <Box color={layer.visible ? '#B7FF35' : '#2A3A2C'}>
                    {getLayerIcon(layer.type)}
                  </Box>
                  <Text
                    flex={1}
                    color={layer.visible ? '#F4F7F0' : '#A5B1A7'}
                    fontSize="xs"
                    fontWeight="500"
                    noOfLines={1}
                    textDecoration={layer.visible ? 'none' : 'line-through'}
                    opacity={layer.visible ? 1 : 0.5}
                  >
                    {layer.name}
                  </Text>
                  <IconButton
                    aria-label="Toggle visibility"
                    icon={
                      layer.visible ? (
                        <FiEye size={12} />
                      ) : (
                        <FiEyeOff size={12} />
                      )
                    }
                    size="xs"
                    variant="ghost"
                    color={layer.visible ? '#A5B1A7' : '#2A3A2C'}
                    _hover={{ color: '#B7FF35' }}
                    onClick={() => toggleLayerVisibility(layer.id)}
                  />
                </Flex>
              ))}
            </VStack>

            {/* Layer Actions */}
            <Box px={4} py={3}>
              <Button
                w="100%"
                size="xs"
                variant="outline"
                borderColor="#2A3A2C"
                color="#A5B1A7"
                borderRadius="lg"
                _hover={{ borderColor: '#B7FF35', color: '#F4F7F0' }}
                leftIcon={<FiPlus size={12} />}
                fontSize="xs"
              >
                Add Layer
              </Button>
            </Box>
          </Box>
        </Flex>
      </Box>
    </WorkspaceLayout>
  );
};

export default ImagineCanvas;
