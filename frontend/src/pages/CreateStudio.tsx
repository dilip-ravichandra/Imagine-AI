import React, { useState } from 'react';
import {
  Box,
  Flex,
  Grid,
  GridItem,
  Text,
  Heading,
  Textarea,
  Input,
  Button,
  Select,
  Image,
  Spinner,
  HStack,
  VStack,
  IconButton,
} from '@chakra-ui/react';
import { DownloadIcon } from '@chakra-ui/icons';
import WorkspaceLayout from '../components/WorkspaceLayout';

const styleOptions = [
  'Realistic',
  'Cartoon',
  '3D',
  'Sketch',
  'Fantasy',
  'Illustration',
  'Vector',
  'Anime',
];

const modelOptions = [
  'SD-Turbo',
  'SD 1.5',
  'MobileDiffusion',
  'BK-SDM-Tiny',
];

const aspectOptions = ['1:1', '16:9', '9:16', '4:3', '3:4'];
const qualityOptions = ['Quick', 'Balanced', 'Best'];

const CreateStudio: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [negativePrompt, setNegativePrompt] = useState('');
  const [style, setStyle] = useState('Realistic');
  const [model, setModel] = useState('SD-Turbo');
  const [aspect, setAspect] = useState('1:1');
  const [quality, setQuality] = useState('Balanced');
  const [numOutputs, setNumOutputs] = useState(1);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedImages, setGeneratedImages] = useState<string[]>([]);

  const handleGenerate = () => {
    if (!prompt.trim()) return;
    setIsGenerating(true);
    setGeneratedImages([]);

    // Simulate generation
    setTimeout(() => {
      const images = Array.from({ length: numOutputs }, (_, i) =>
        `https://picsum.photos/seed/gen${Date.now() + i}/512/512`
      );
      setGeneratedImages(images);
      setIsGenerating(false);
    }, 3000);
  };

  const handleEnhance = () => {
    if (!prompt.trim()) return;
    setPrompt(
      (prev) =>
        `${prev}, cinematic lighting, ultra-detailed, 8k resolution, masterpiece, professional composition, volumetric fog, ray tracing`
    );
  };

  const selectStyles = {
    bg: '#0F1A11',
    color: '#F4F7F0',
    border: '1px solid',
    borderColor: '#2A3A2C',
    borderRadius: '10px',
    fontSize: 'sm',
    _hover: { borderColor: '#8DDB39' },
    _focus: { borderColor: '#B7FF35', boxShadow: '0 0 0 1px #B7FF35' },
    sx: {
      option: {
        bg: '#111713',
        color: '#F4F7F0',
      },
    },
  };

  return (
    <WorkspaceLayout>
      <Box px={{ base: 4, md: 8 }} py={8} maxW="1400px" mx="auto">
        {/* Header */}
        <Flex align="center" mb={8} gap={3}>
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
            🎨
          </Box>
          <Box>
            <Heading fontSize="2xl" color="#F4F7F0" fontWeight="700">
              Generate Image
            </Heading>
            <Text fontSize="sm" color="#A5B1A7">
              Turn your imagination into stunning visuals
            </Text>
          </Box>
        </Flex>

        <Flex gap={6} direction={{ base: 'column', lg: 'row' }}>
          {/* Left Panel — Controls */}
          <Box flex="7" minW={0}>
            <VStack spacing={5} align="stretch">
              {/* Prompt */}
              <Box>
                <Text fontSize="sm" fontWeight="600" color="#F4F7F0" mb={2}>
                  Prompt
                </Text>
                <Textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="A futuristic city with green energy, at sunset, cinematic, ultra realistic"
                  bg="#0F1A11"
                  color="#F4F7F0"
                  border="1px solid"
                  borderColor="#2A3A2C"
                  borderRadius="12px"
                  rows={5}
                  fontSize="sm"
                  resize="vertical"
                  _placeholder={{ color: '#5a6b5c' }}
                  _hover={{ borderColor: '#8DDB39' }}
                  _focus={{
                    borderColor: '#B7FF35',
                    boxShadow: '0 0 0 1px #B7FF35',
                  }}
                />
                <Button
                  mt={2}
                  size="sm"
                  variant="outline"
                  borderColor="#B7FF35"
                  color="#B7FF35"
                  borderRadius="8px"
                  fontWeight="600"
                  _hover={{
                    bg: 'rgba(183,255,53,0.1)',
                    borderColor: '#B7FF35',
                  }}
                  onClick={handleEnhance}
                >
                  ✨ Enhance Prompt
                </Button>
              </Box>

              {/* Settings Grid */}
              <Grid templateColumns="repeat(2, 1fr)" gap={4}>
                <GridItem>
                  <Text fontSize="xs" fontWeight="600" color="#A5B1A7" mb={1.5} textTransform="uppercase" letterSpacing="0.05em">
                    Style
                  </Text>
                  <Select
                    value={style}
                    onChange={(e) => setStyle(e.target.value)}
                    {...selectStyles}
                  >
                    {styleOptions.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </Select>
                </GridItem>
                <GridItem>
                  <Text fontSize="xs" fontWeight="600" color="#A5B1A7" mb={1.5} textTransform="uppercase" letterSpacing="0.05em">
                    Model
                  </Text>
                  <Select
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    {...selectStyles}
                  >
                    {modelOptions.map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                  </Select>
                </GridItem>
                <GridItem>
                  <Text fontSize="xs" fontWeight="600" color="#A5B1A7" mb={1.5} textTransform="uppercase" letterSpacing="0.05em">
                    Aspect Ratio
                  </Text>
                  <Select
                    value={aspect}
                    onChange={(e) => setAspect(e.target.value)}
                    {...selectStyles}
                  >
                    {aspectOptions.map((a) => (
                      <option key={a} value={a}>
                        {a}
                      </option>
                    ))}
                  </Select>
                </GridItem>
                <GridItem>
                  <Text fontSize="xs" fontWeight="600" color="#A5B1A7" mb={1.5} textTransform="uppercase" letterSpacing="0.05em">
                    Quality
                  </Text>
                  <Select
                    value={quality}
                    onChange={(e) => setQuality(e.target.value)}
                    {...selectStyles}
                  >
                    {qualityOptions.map((q) => (
                      <option key={q} value={q}>
                        {q}
                      </option>
                    ))}
                  </Select>
                </GridItem>
              </Grid>

              {/* Negative Prompt */}
              <Box>
                <Text fontSize="xs" fontWeight="600" color="#A5B1A7" mb={1.5} textTransform="uppercase" letterSpacing="0.05em">
                  Negative Prompt (optional)
                </Text>
                <Input
                  value={negativePrompt}
                  onChange={(e) => setNegativePrompt(e.target.value)}
                  placeholder="blurry, low quality, distorted, watermark, text"
                  bg="#0F1A11"
                  color="#F4F7F0"
                  border="1px solid"
                  borderColor="#2A3A2C"
                  borderRadius="10px"
                  fontSize="sm"
                  _placeholder={{ color: '#5a6b5c' }}
                  _hover={{ borderColor: '#8DDB39' }}
                  _focus={{
                    borderColor: '#B7FF35',
                    boxShadow: '0 0 0 1px #B7FF35',
                  }}
                />
              </Box>

              {/* Number of Outputs */}
              <Box>
                <Text fontSize="xs" fontWeight="600" color="#A5B1A7" mb={2} textTransform="uppercase" letterSpacing="0.05em">
                  Number of Outputs
                </Text>
                <HStack spacing={3}>
                  {[1, 2, 3, 4].map((n) => (
                    <Button
                      key={n}
                      size="sm"
                      w="48px"
                      h="40px"
                      borderRadius="10px"
                      fontWeight="700"
                      fontSize="sm"
                      bg={numOutputs === n ? '#B7FF35' : '#0F1A11'}
                      color={numOutputs === n ? '#080B0A' : '#A5B1A7'}
                      border="1px solid"
                      borderColor={numOutputs === n ? '#B7FF35' : '#2A3A2C'}
                      _hover={{
                        bg: numOutputs === n ? '#8DDB39' : '#1A2A1C',
                        borderColor: '#B7FF35',
                      }}
                      onClick={() => setNumOutputs(n)}
                    >
                      {n}
                    </Button>
                  ))}
                </HStack>
              </Box>

              {/* Generate Button */}
              <Button
                w="100%"
                h="52px"
                bg="#B7FF35"
                color="#080B0A"
                borderRadius="12px"
                fontWeight="700"
                fontSize="md"
                _hover={{
                  bg: '#8DDB39',
                  transform: 'translateY(-1px)',
                  boxShadow: '0 4px 20px rgba(183,255,53,0.3)',
                }}
                _active={{ transform: 'scale(0.98)' }}
                transition="all 0.2s ease"
                onClick={handleGenerate}
                isLoading={isGenerating}
                loadingText="Generating..."
                spinner={<Spinner size="sm" color="#080B0A" />}
              >
                ✨ Generate
              </Button>
            </VStack>
          </Box>

          {/* Right Panel — Outputs */}
          <Box flex="3" minW={0}>
            <Box
              bg="#111713"
              border="1px solid"
              borderColor="#2A3A2C"
              borderRadius="14px"
              p={5}
              minH="500px"
              position="relative"
            >
              <Heading fontSize="md" color="#F4F7F0" fontWeight="600" mb={4}>
                Outputs
              </Heading>

              {isGenerating ? (
                <Flex
                  direction="column"
                  align="center"
                  justify="center"
                  minH="350px"
                  gap={4}
                >
                  <Box
                    w="64px"
                    h="64px"
                    borderRadius="14px"
                    bg="rgba(183,255,53,0.08)"
                    display="flex"
                    alignItems="center"
                    justifyContent="center"
                    sx={{
                      animation: 'pulse 1.8s ease-in-out infinite',
                      '@keyframes pulse': {
                        '0%, 100%': {
                          transform: 'scale(1)',
                          opacity: 0.7,
                        },
                        '50%': {
                          transform: 'scale(1.12)',
                          opacity: 1,
                        },
                      },
                    }}
                  >
                    <Text fontSize="2xl">✨</Text>
                  </Box>
                  <Text fontSize="sm" color="#A5B1A7" fontWeight="500">
                    Creating your masterpiece...
                  </Text>
                  <Box
                    w="120px"
                    h="3px"
                    borderRadius="full"
                    bg="#182019"
                    overflow="hidden"
                  >
                    <Box
                      h="100%"
                      borderRadius="full"
                      bg="#B7FF35"
                      sx={{
                        animation: 'loading 1.5s ease-in-out infinite',
                        '@keyframes loading': {
                          '0%': { width: '0%', ml: '0%' },
                          '50%': { width: '70%', ml: '15%' },
                          '100%': { width: '0%', ml: '100%' },
                        },
                      }}
                    />
                  </Box>
                </Flex>
              ) : generatedImages.length > 0 ? (
                <VStack spacing={4} align="stretch">
                  {generatedImages.map((src, i) => (
                    <Box key={i}>
                      <Image
                        src={src}
                        alt={`Generated ${i + 1}`}
                        w="100%"
                        borderRadius="10px"
                        objectFit="cover"
                      />
                      <HStack mt={2} spacing={2}>
                        <Button
                          size="sm"
                          flex={1}
                          bg="#182019"
                          color="#F4F7F0"
                          borderRadius="8px"
                          fontSize="xs"
                          fontWeight="600"
                          border="1px solid"
                          borderColor="#2A3A2C"
                          _hover={{ bg: '#1A2A1C', borderColor: '#8DDB39' }}
                          leftIcon={<DownloadIcon />}
                          onClick={() => window.open(src, '_blank')}
                        >
                          Download
                        </Button>
                        <Button
                          size="sm"
                          flex={1}
                          bg="#182019"
                          color="#B7FF35"
                          borderRadius="8px"
                          fontSize="xs"
                          fontWeight="600"
                          border="1px solid"
                          borderColor="#2A3A2C"
                          _hover={{ bg: '#1A2A1C', borderColor: '#B7FF35' }}
                        >
                          ⭐ Save to Gallery
                        </Button>
                      </HStack>
                    </Box>
                  ))}
                </VStack>
              ) : (
                <Flex
                  direction="column"
                  align="center"
                  justify="center"
                  minH="350px"
                  gap={3}
                >
                  <Box
                    w="80px"
                    h="80px"
                    borderRadius="16px"
                    border="2px dashed"
                    borderColor="#2A3A2C"
                    display="flex"
                    alignItems="center"
                    justifyContent="center"
                  >
                    <Text fontSize="2xl" opacity={0.4}>
                      🖼️
                    </Text>
                  </Box>
                  <Text fontSize="sm" color="#A5B1A7" textAlign="center" maxW="200px">
                    Your generated images will appear here
                  </Text>
                </Flex>
              )}
            </Box>
          </Box>
        </Flex>
      </Box>
    </WorkspaceLayout>
  );
};

export default CreateStudio;
