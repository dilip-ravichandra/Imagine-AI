import React, { useState } from 'react';
import {
  Box, Flex, Text, Heading, Button,
} from '@chakra-ui/react';
import WorkspaceLayout from '../components/WorkspaceLayout';

const DownloadIcon: React.FC = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" />
  </svg>
);

const TABS = ['Comparison', 'Latency', 'Quality', 'GPU/VRAM'];

interface ModelData {
  name: string;
  fid: number;
  clip: number;
  latency: number;
  quality: number;
  vram: number;
  color: string;
}

const MODELS: ModelData[] = [
  { name: 'SD 1.5', fid: 13.54, clip: 0.312, latency: 4.21, quality: 3.5, vram: 6.8, color: '#B7FF35' },
  { name: 'SD-Turbo', fid: 35.6, clip: 0.291, latency: 0.82, quality: 2.9, vram: 4.2, color: '#8DDB39' },
  { name: 'MobileDiffusion', fid: 15.67, clip: 0.290, latency: 0.62, quality: 2.0, vram: 2.8, color: '#FFB800' },
  { name: 'BK-SDM-Tiny', fid: 16.21, clip: 0.295, latency: 0.76, quality: 1.8, vram: 1.6, color: '#4ECDC4' },
];

const StarRating: React.FC<{ value: number; max?: number }> = ({ value, max = 5 }) => {
  const fullStars = Math.floor(value);
  const hasHalf = value - fullStars >= 0.5;
  return (
    <Flex gap="1px" align="center">
      {Array.from({ length: max }, (_, i) => (
        <Box key={i} color={i < fullStars ? '#FFB800' : i === fullStars && hasHalf ? '#FFB800' : '#2A3A2C'} fontSize="xs">
          ★
        </Box>
      ))}
      <Text color="#A5B1A7" fontSize="xs" ml={1}>
        {value.toFixed(1)}
      </Text>
    </Flex>
  );
};

const ModelPerformance: React.FC = () => {
  const [activeTab, setActiveTab] = useState('Comparison');

  const maxLatency = Math.max(...MODELS.map((m) => m.latency));
  const maxFid = Math.max(...MODELS.map((m) => m.fid));
  const maxVram = Math.max(...MODELS.map((m) => m.vram));

  return (
    <WorkspaceLayout>
      <Box p={8} minH="100vh" bg="#080B0A">
        {/* Header */}
        <Flex align="center" justify="space-between" mb={6}>
          <Box>
            <Heading size="lg" color="#F4F7F0" fontWeight={700}>
              Model Performance
            </Heading>
            <Text color="#A5B1A7" mt={1} fontSize="sm">
              Compare benchmarks, latency, quality, and resource usage across models
            </Text>
          </Box>
          <Button
            bg="#B7FF35"
            color="#080B0A"
            borderRadius="10px"
            fontWeight={700}
            size="sm"
            _hover={{ bg: '#8DDB39' }}
            leftIcon={<DownloadIcon />}
          >
            Export Report
          </Button>
        </Flex>

        {/* Tabs */}
        <Flex gap={2} mb={7}>
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
              transition="all 0.2s ease"
            >
              {tab}
            </Button>
          ))}
        </Flex>

        {/* Summary Cards */}
        <Flex gap={4} mb={7}>
          {[
            { label: 'Best FID Score', value: '13.54', sub: 'SD 1.5', color: '#B7FF35' },
            { label: 'Best CLIP Score', value: '0.312', sub: 'SD 1.5', color: '#8DDB39' },
            { label: 'Fastest Inference', value: '0.62s', sub: 'MobileDiffusion', color: '#FFB800' },
            { label: 'Lowest VRAM', value: '1.6 GB', sub: 'BK-SDM-Tiny', color: '#4ECDC4' },
          ].map((card) => (
            <Box
              key={card.label}
              flex={1}
              bg="#111713"
              borderRadius="14px"
              border="1px solid #2A3A2C"
              p={5}
              _hover={{ borderColor: card.color, transform: 'translateY(-2px)' }}
              transition="all 0.3s ease"
            >
              <Text color="#A5B1A7" fontSize="xs" textTransform="uppercase" letterSpacing="0.08em" mb={2}>
                {card.label}
              </Text>
              <Text color={card.color} fontSize="2xl" fontWeight={700} lineHeight={1}>
                {card.value}
              </Text>
              <Text color="#A5B1A7" fontSize="xs" mt={1}>{card.sub}</Text>
            </Box>
          ))}
        </Flex>

        <Flex gap={6}>
          {/* Data Table */}
          <Box flex={2}>
            <Box
              bg="#111713"
              borderRadius="16px"
              border="1px solid #2A3A2C"
              overflow="hidden"
            >
              {/* Table Header */}
              <Flex
                bg="#0D120E"
                px={5}
                py={3}
                borderBottom="1px solid #2A3A2C"
                fontSize="xs"
                color="#A5B1A7"
                textTransform="uppercase"
                letterSpacing="0.08em"
                fontWeight={600}
              >
                <Box flex={2}>Model</Box>
                <Box flex={1} textAlign="right">FID ↓</Box>
                <Box flex={1} textAlign="right">CLIP ↑</Box>
                <Box flex={1} textAlign="right">Latency (s)</Box>
                <Box flex={1.2} textAlign="center">Quality</Box>
                <Box flex={1} textAlign="right">VRAM (GB)</Box>
              </Flex>

              {/* Table Rows */}
              {MODELS.map((model, i) => (
                <Flex
                  key={model.name}
                  px={5}
                  py={4}
                  borderBottom={i < MODELS.length - 1 ? '1px solid #2A3A2C' : 'none'}
                  bg={i % 2 === 1 ? 'rgba(13,18,14,0.5)' : 'transparent'}
                  _hover={{ bg: '#1A2A1C' }}
                  transition="background 0.2s ease"
                  align="center"
                  fontSize="sm"
                >
                  <Box flex={2}>
                    <Flex align="center" gap={3}>
                      <Box w="10px" h="10px" borderRadius="full" bg={model.color} flexShrink={0} />
                      <Text color="#F4F7F0" fontWeight={600}>{model.name}</Text>
                    </Flex>
                  </Box>
                  <Box flex={1} textAlign="right">
                    <Text color={model.fid === Math.min(...MODELS.map((m) => m.fid)) ? '#B7FF35' : '#F4F7F0'} fontWeight={500}>
                      {model.fid.toFixed(2)}
                    </Text>
                  </Box>
                  <Box flex={1} textAlign="right">
                    <Text color={model.clip === Math.max(...MODELS.map((m) => m.clip)) ? '#B7FF35' : '#F4F7F0'} fontWeight={500}>
                      {model.clip.toFixed(3)}
                    </Text>
                  </Box>
                  <Box flex={1} textAlign="right">
                    <Text color={model.latency === Math.min(...MODELS.map((m) => m.latency)) ? '#B7FF35' : '#F4F7F0'} fontWeight={500}>
                      {model.latency.toFixed(2)}
                    </Text>
                  </Box>
                  <Box flex={1.2}>
                    <Flex justify="center">
                      <StarRating value={model.quality} />
                    </Flex>
                  </Box>
                  <Box flex={1} textAlign="right">
                    <Text color={model.vram === Math.min(...MODELS.map((m) => m.vram)) ? '#B7FF35' : '#F4F7F0'} fontWeight={500}>
                      {model.vram.toFixed(1)}
                    </Text>
                  </Box>
                </Flex>
              ))}
            </Box>

            {/* Additional Metrics */}
            <Box
              bg="#111713"
              borderRadius="16px"
              border="1px solid #2A3A2C"
              p={5}
              mt={6}
            >
              <Text color="#F4F7F0" fontWeight={600} mb={4}>Key Insights</Text>
              <Flex direction="column" gap={3}>
                {[
                  { icon: '⚡', text: 'MobileDiffusion achieves 6.8× faster inference than SD 1.5 with competitive quality', color: '#FFB800' },
                  { icon: '🎯', text: 'SD 1.5 leads in both FID and CLIP metrics, indicating superior generation fidelity', color: '#B7FF35' },
                  { icon: '💾', text: 'BK-SDM-Tiny uses only 1.6 GB VRAM — ideal for edge deployment scenarios', color: '#4ECDC4' },
                  { icon: '🔄', text: 'SD-Turbo trades quality for speed with 5× faster inference than SD 1.5', color: '#8DDB39' },
                ].map((insight, i) => (
                  <Flex
                    key={i}
                    align="flex-start"
                    gap={3}
                    p={3}
                    bg="#0D120E"
                    borderRadius="10px"
                    border="1px solid #2A3A2C"
                  >
                    <Text fontSize="md">{insight.icon}</Text>
                    <Text color="#A5B1A7" fontSize="sm" lineHeight="tall">{insight.text}</Text>
                  </Flex>
                ))}
              </Flex>
            </Box>
          </Box>

          {/* Bar Charts */}
          <Box flex={1}>
            {/* Inference Time Chart */}
            <Box
              bg="#111713"
              borderRadius="16px"
              border="1px solid #2A3A2C"
              p={5}
              mb={6}
            >
              <Text color="#F4F7F0" fontWeight={600} mb={1}>Inference Time (s)</Text>
              <Text color="#A5B1A7" fontSize="xs" mb={5}>Lower is better</Text>
              <Flex direction="column" gap={4}>
                {MODELS.map((model) => (
                  <Box key={model.name}>
                    <Flex justify="space-between" mb={1.5}>
                      <Text color="#A5B1A7" fontSize="xs" fontWeight={500}>{model.name}</Text>
                      <Text color="#F4F7F0" fontSize="xs" fontWeight={600}>{model.latency.toFixed(2)}s</Text>
                    </Flex>
                    <Box bg="#0D120E" borderRadius="full" h="12px" overflow="hidden">
                      <Box
                        bg={model.color}
                        h="100%"
                        w={`${(model.latency / maxLatency) * 100}%`}
                        borderRadius="full"
                        transition="width 0.8s ease"
                      />
                    </Box>
                  </Box>
                ))}
              </Flex>
            </Box>

            {/* FID Score Chart */}
            <Box
              bg="#111713"
              borderRadius="16px"
              border="1px solid #2A3A2C"
              p={5}
              mb={6}
            >
              <Text color="#F4F7F0" fontWeight={600} mb={1}>FID Score</Text>
              <Text color="#A5B1A7" fontSize="xs" mb={5}>Lower is better</Text>
              <Flex direction="column" gap={4}>
                {MODELS.map((model) => (
                  <Box key={model.name}>
                    <Flex justify="space-between" mb={1.5}>
                      <Text color="#A5B1A7" fontSize="xs" fontWeight={500}>{model.name}</Text>
                      <Text color="#F4F7F0" fontSize="xs" fontWeight={600}>{model.fid.toFixed(2)}</Text>
                    </Flex>
                    <Box bg="#0D120E" borderRadius="full" h="12px" overflow="hidden">
                      <Box
                        bg={model.color}
                        h="100%"
                        w={`${(model.fid / maxFid) * 100}%`}
                        borderRadius="full"
                        transition="width 0.8s ease"
                      />
                    </Box>
                  </Box>
                ))}
              </Flex>
            </Box>

            {/* VRAM Chart */}
            <Box
              bg="#111713"
              borderRadius="16px"
              border="1px solid #2A3A2C"
              p={5}
            >
              <Text color="#F4F7F0" fontWeight={600} mb={1}>GPU VRAM (GB)</Text>
              <Text color="#A5B1A7" fontSize="xs" mb={5}>Lower is better for edge deployment</Text>
              <Flex direction="column" gap={4}>
                {MODELS.map((model) => (
                  <Box key={model.name}>
                    <Flex justify="space-between" mb={1.5}>
                      <Text color="#A5B1A7" fontSize="xs" fontWeight={500}>{model.name}</Text>
                      <Text color="#F4F7F0" fontSize="xs" fontWeight={600}>{model.vram.toFixed(1)} GB</Text>
                    </Flex>
                    <Box bg="#0D120E" borderRadius="full" h="12px" overflow="hidden">
                      <Box
                        bg={model.color}
                        h="100%"
                        w={`${(model.vram / maxVram) * 100}%`}
                        borderRadius="full"
                        transition="width 0.8s ease"
                      />
                    </Box>
                  </Box>
                ))}
              </Flex>
            </Box>
          </Box>
        </Flex>
      </Box>
    </WorkspaceLayout>
  );
};

export default ModelPerformance;
