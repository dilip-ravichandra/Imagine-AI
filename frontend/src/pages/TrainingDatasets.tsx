import React, { useState } from 'react';
import {
  Box, Flex, Text, Heading, Button, Grid, GridItem,
  Modal, ModalOverlay, ModalContent, ModalHeader, ModalBody, ModalFooter, ModalCloseButton,
  Select, Input,
} from '@chakra-ui/react';
import WorkspaceLayout from '../components/WorkspaceLayout';

const BoltIcon: React.FC = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#B7FF35" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
  </svg>
);

const DatabaseIcon: React.FC = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#8DDB39" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" /><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
  </svg>
);

const CheckpointIcon: React.FC = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#FFB800" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />
  </svg>
);

const LoraIcon: React.FC = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#4ECDC4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3" /><path d="M12 1v6m0 6v6" /><path d="M1 12h6m6 0h6" /><path d="M4.22 4.22l4.24 4.24m3.08 3.08l4.24 4.24" /><path d="M19.78 4.22l-4.24 4.24m-3.08 3.08l-4.24 4.24" />
  </svg>
);

const PlusIcon: React.FC = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
  </svg>
);

const FolderIcon: React.FC = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#A5B1A7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
  </svg>
);

interface StatCard {
  icon: React.ReactNode;
  label: string;
  value: number;
  sub: string;
  color: string;
}

const STATS: StatCard[] = [
  { icon: <BoltIcon />, label: 'Training Jobs', value: 4, sub: 'active', color: '#B7FF35' },
  { icon: <DatabaseIcon />, label: 'Datasets', value: 12, sub: 'uploaded', color: '#8DDB39' },
  { icon: <CheckpointIcon />, label: 'Checkpoints', value: 36, sub: 'saved', color: '#FFB800' },
  { icon: <LoraIcon />, label: 'LoRA Adapters', value: 8, sub: 'trained', color: '#4ECDC4' },
];

interface TrainingJob {
  name: string;
  model: string;
  status: 'Active' | 'Complete' | 'Queued' | 'Failed';
  progress: number;
  epoch: string;
  eta: string;
}

const TRAINING_JOBS: TrainingJob[] = [
  { name: 'SD 1.5 Fine-tune (Custom)', model: 'SD 1.5', status: 'Active', progress: 72, epoch: '36 / 50', eta: '~2h 15m' },
  { name: 'LoRA Portrait Style', model: 'SDXL', status: 'Active', progress: 45, epoch: '22 / 50', eta: '~4h 30m' },
  { name: 'Anime Style Transfer', model: 'SD 1.5', status: 'Complete', progress: 100, epoch: '50 / 50', eta: 'Done' },
  { name: 'Product Photography', model: 'SD-Turbo', status: 'Queued', progress: 0, epoch: '0 / 30', eta: 'Waiting' },
  { name: 'Architecture LoRA v2', model: 'SDXL', status: 'Active', progress: 18, epoch: '9 / 50', eta: '~6h 45m' },
  { name: 'Landscape HDR Model', model: 'SD 1.5', status: 'Failed', progress: 62, epoch: '31 / 50', eta: 'Error' },
];

interface Dataset {
  name: string;
  images: number;
  size: string;
  type: string;
  lastUpdated: string;
}

const DATASETS: Dataset[] = [
  { name: 'Custom Portraits v3', images: 2450, size: '4.2 GB', type: 'Fine-tune', lastUpdated: 'Nov 5, 2026' },
  { name: 'Anime Characters', images: 8200, size: '12.1 GB', type: 'Style Transfer', lastUpdated: 'Nov 3, 2026' },
  { name: 'Product Shots', images: 1800, size: '3.6 GB', type: 'DreamBooth', lastUpdated: 'Oct 28, 2026' },
  { name: 'Architectural Renders', images: 3100, size: '5.8 GB', type: 'LoRA', lastUpdated: 'Oct 20, 2026' },
];

const statusColor = (status: TrainingJob['status']) => {
  switch (status) {
    case 'Active': return '#B7FF35';
    case 'Complete': return '#8DDB39';
    case 'Queued': return '#FFB800';
    case 'Failed': return '#FF4444';
  }
};

const TrainingDatasets: React.FC = () => {
  const [jobs, setJobs] = useState<TrainingJob[]>(TRAINING_JOBS);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [jobName, setJobName] = useState('Multimodal SD Fine-tune');
  const [selectedModel, setSelectedModel] = useState('Stable Diffusion 1.5');
  const [selectedDataset, setSelectedDataset] = useState('Custom Portraits v3');
  const [batchSize, setBatchSize] = useState('16');
  const [epochs, setEpochs] = useState('50');
  const [learningRate, setLearningRate] = useState('1e-4');

  const handleStartTraining = () => {
    const newJob: TrainingJob = {
      name: jobName,
      model: selectedModel,
      status: 'Active',
      progress: 2,
      epoch: `1 / ${epochs}`,
      eta: '~3h 40m',
    };
    setJobs([newJob, ...jobs]);
    setIsModalOpen(false);
  };
  return (
    <WorkspaceLayout>
      <Box p={8} minH="100vh" bg="#080B0A">
        {/* Header */}
        <Flex align="center" justify="space-between" mb={7}>
          <Box>
            <Heading size="lg" color="#F4F7F0" fontWeight={700}>
              Training & Datasets
            </Heading>
            <Text color="#A5B1A7" mt={1} fontSize="sm">
              Manage training jobs, datasets, checkpoints, and LoRA adapters
            </Text>
          </Box>
          <Button
            bg="#B7FF35"
            color="#080B0A"
            borderRadius="10px"
            fontWeight={700}
            _hover={{ bg: '#8DDB39' }}
            _active={{ bg: '#7BC82E' }}
            leftIcon={<PlusIcon />}
            onClick={() => setIsModalOpen(true)}
          >
            Start New Training
          </Button>
        </Flex>

        {/* Stats Cards */}
        <Grid templateColumns="repeat(4, 1fr)" gap={5} mb={8}>
          {STATS.map((stat) => (
            <GridItem key={stat.label}>
              <Box
                bg="#111713"
                borderRadius="14px"
                border="1px solid #2A3A2C"
                p={5}
                _hover={{
                  borderColor: stat.color,
                  transform: 'translateY(-2px)',
                  boxShadow: `0 8px 30px ${stat.color}10`,
                }}
                transition="all 0.3s ease"
                cursor="pointer"
              >
                <Flex justify="space-between" align="flex-start" mb={3}>
                  <Box
                    p={2.5}
                    borderRadius="10px"
                    bg={`${stat.color}15`}
                    border={`1px solid ${stat.color}30`}
                  >
                    {stat.icon}
                  </Box>
                  <Box
                    w="8px"
                    h="8px"
                    borderRadius="full"
                    bg={stat.color}
                    opacity={0.6}
                  />
                </Flex>
                <Text
                  color="#F4F7F0"
                  fontSize="3xl"
                  fontWeight={700}
                  lineHeight={1}
                  mb={1}
                >
                  {stat.value}
                </Text>
                <Flex align="center" gap={1.5}>
                  <Text color="#A5B1A7" fontSize="sm">{stat.label}</Text>
                  <Text color={stat.color} fontSize="xs">• {stat.sub}</Text>
                </Flex>
              </Box>
            </GridItem>
          ))}
        </Grid>

        {/* Training Progress */}
        <Box mb={8}>
          <Flex justify="space-between" align="center" mb={4}>
            <Box>
              <Text color="#F4F7F0" fontSize="lg" fontWeight={600}>Training Progress</Text>
              <Text color="#A5B1A7" fontSize="sm">Monitor active and completed training jobs</Text>
            </Box>
            <Flex gap={2}>
              {['All', 'Active', 'Complete', 'Queued'].map((f) => (
                <Button
                  key={f}
                  size="xs"
                  bg={f === 'All' ? 'rgba(183,255,53,0.1)' : 'transparent'}
                  color={f === 'All' ? '#B7FF35' : '#A5B1A7'}
                  border="1px solid"
                  borderColor={f === 'All' ? 'rgba(183,255,53,0.3)' : '#2A3A2C'}
                  borderRadius="6px"
                  _hover={{ bg: '#1A2A1C', color: '#F4F7F0' }}
                >
                  {f}
                </Button>
              ))}
            </Flex>
          </Flex>

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
              <Box flex={2.5}>Job Name</Box>
              <Box flex={1}>Model</Box>
              <Box flex={1} textAlign="center">Status</Box>
              <Box flex={2}>Progress</Box>
              <Box flex={1} textAlign="center">Epoch</Box>
              <Box flex={1} textAlign="right">ETA</Box>
            </Flex>

            {/* Table Rows */}
            {jobs.map((job, i) => (
              <Flex
                key={job.name}
                px={5}
                py={4}
                borderBottom={i < jobs.length - 1 ? '1px solid #2A3A2C' : 'none'}
                bg={i % 2 === 1 ? 'rgba(13,18,14,0.5)' : 'transparent'}
                _hover={{ bg: '#1A2A1C' }}
                transition="background 0.2s ease"
                align="center"
                fontSize="sm"
              >
                <Box flex={2.5}>
                  <Text color="#F4F7F0" fontWeight={600}>{job.name}</Text>
                </Box>
                <Box flex={1}>
                  <Box
                    as="span"
                    bg="#0D120E"
                    color="#A5B1A7"
                    px={2}
                    py={0.5}
                    borderRadius="4px"
                    fontSize="xs"
                    border="1px solid #2A3A2C"
                  >
                    {job.model}
                  </Box>
                </Box>
                <Box flex={1} textAlign="center">
                  <Flex align="center" justify="center" gap={1.5}>
                    <Box
                      w="7px"
                      h="7px"
                      borderRadius="full"
                      bg={statusColor(job.status)}
                      boxShadow={job.status === 'Active' ? `0 0 8px ${statusColor(job.status)}` : 'none'}
                    />
                    <Text color={statusColor(job.status)} fontSize="xs" fontWeight={600}>
                      {job.status}
                    </Text>
                  </Flex>
                </Box>
                <Box flex={2} px={2}>
                  <Flex align="center" gap={3}>
                    <Box flex={1} bg="#0D120E" borderRadius="full" h="8px" overflow="hidden">
                      <Box
                        bg={job.status === 'Failed' ? '#FF4444' : '#B7FF35'}
                        h="100%"
                        w={`${job.progress}%`}
                        borderRadius="full"
                        transition="width 0.5s ease"
                      />
                    </Box>
                    <Text
                      color={job.progress === 100 ? '#8DDB39' : '#F4F7F0'}
                      fontSize="xs"
                      fontWeight={600}
                      minW="35px"
                      textAlign="right"
                    >
                      {job.progress}%
                    </Text>
                  </Flex>
                </Box>
                <Box flex={1} textAlign="center">
                  <Text color="#A5B1A7" fontSize="xs">{job.epoch}</Text>
                </Box>
                <Box flex={1} textAlign="right">
                  <Text
                    color={job.status === 'Failed' ? '#FF4444' : '#A5B1A7'}
                    fontSize="xs"
                    fontWeight={job.status === 'Failed' ? 600 : 400}
                  >
                    {job.eta}
                  </Text>
                </Box>
              </Flex>
            ))}
          </Box>
        </Box>

        {/* Recent Datasets */}
        <Box>
          <Flex justify="space-between" align="center" mb={4}>
            <Box>
              <Text color="#F4F7F0" fontSize="lg" fontWeight={600}>Recent Datasets</Text>
              <Text color="#A5B1A7" fontSize="sm">Your uploaded training datasets</Text>
            </Box>
            <Button
              bg="transparent"
              color="#B7FF35"
              border="1px solid #B7FF35"
              borderRadius="10px"
              size="sm"
              _hover={{ bg: 'rgba(183,255,53,0.1)' }}
              leftIcon={<PlusIcon />}
            >
              Upload Dataset
            </Button>
          </Flex>

          <Grid templateColumns="repeat(auto-fill, minmax(280px, 1fr))" gap={5}>
            {DATASETS.map((dataset) => (
              <GridItem key={dataset.name}>
                <Box
                  bg="#111713"
                  borderRadius="14px"
                  border="1px solid #2A3A2C"
                  p={5}
                  _hover={{
                    borderColor: '#B7FF35',
                    transform: 'translateY(-2px)',
                    boxShadow: '0 8px 30px rgba(183,255,53,0.06)',
                  }}
                  transition="all 0.3s ease"
                  cursor="pointer"
                >
                  <Flex align="center" gap={3} mb={4}>
                    <Box
                      p={2}
                      borderRadius="8px"
                      bg="rgba(141,219,57,0.1)"
                      border="1px solid rgba(141,219,57,0.2)"
                    >
                      <FolderIcon />
                    </Box>
                    <Box flex={1}>
                      <Text color="#F4F7F0" fontWeight={600} fontSize="sm">
                        {dataset.name}
                      </Text>
                      <Text color="#A5B1A7" fontSize="xs">{dataset.type}</Text>
                    </Box>
                  </Flex>

                  {/* Dataset preview thumbnails */}
                  <Flex gap={1} mb={4} borderRadius="8px" overflow="hidden">
                    {[1, 2, 3, 4].map((n) => (
                      <Box
                        key={n}
                        flex={1}
                        h="50px"
                        bg="#0D120E"
                        overflow="hidden"
                      >
                        <Box
                          as="img"
                          src={`https://picsum.photos/seed/${dataset.name.replace(/\s/g, '') + n}/100/100`}
                          alt=""
                          w="100%"
                          h="100%"
                          objectFit="cover"
                        />
                      </Box>
                    ))}
                  </Flex>

                  <Flex justify="space-between" align="center">
                    <Flex gap={4}>
                      <Box>
                        <Text color="#A5B1A7" fontSize="xs">Images</Text>
                        <Text color="#F4F7F0" fontSize="sm" fontWeight={600}>
                          {dataset.images.toLocaleString()}
                        </Text>
                      </Box>
                      <Box>
                        <Text color="#A5B1A7" fontSize="xs">Size</Text>
                        <Text color="#F4F7F0" fontSize="sm" fontWeight={600}>{dataset.size}</Text>
                      </Box>
                    </Flex>
                    <Text color="#A5B1A7" fontSize="xs">{dataset.lastUpdated}</Text>
                  </Flex>
                </Box>
              </GridItem>
            ))}
          </Grid>
        </Box>

        {/* Start New Training Modal */}
        <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} isCentered size="lg">
          <ModalOverlay bg="rgba(0,0,0,0.85)" backdropFilter="blur(6px)" />
          <ModalContent bg="#111713" border="1px solid #2A3A2C" borderRadius="18px" color="#F4F7F0">
            <ModalHeader borderBottom="1px solid #1A2A1C" py={4}>
              <Flex align="center" gap={2}>
                <Box w="28px" h="28px" borderRadius="full" bg="#B7FF35" display="flex" alignItems="center" justifyContent="center" color="#080B0A" fontSize="14px">
                  ⚡
                </Box>
                <Text fontSize="md" fontWeight="bold">
                  Configure Training Job
                </Text>
              </Flex>
            </ModalHeader>
            <ModalCloseButton color="#A5B1A7" />

            <ModalBody py={5}>
              <Box mb={4}>
                <Text fontSize="xs" color="#6B7B6D" mb={1.5} textTransform="uppercase">
                  Job Name
                </Text>
                <Input
                  value={jobName}
                  onChange={(e) => setJobName(e.target.value)}
                  bg="#0F1A11"
                  color="#F4F7F0"
                  border="1px solid #2A3A2C"
                  borderRadius="10px"
                  size="sm"
                  _focus={{ borderColor: '#B7FF35' }}
                />
              </Box>

              <Grid templateColumns="1fr 1fr" gap={4} mb={4}>
                <Box>
                  <Text fontSize="xs" color="#6B7B6D" mb={1.5} textTransform="uppercase">
                    Target Base Model
                  </Text>
                  <Select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    bg="#0F1A11"
                    color="#F4F7F0"
                    border="1px solid #2A3A2C"
                    borderRadius="10px"
                    size="sm"
                  >
                    <option value="Stable Diffusion 1.5" style={{ background: '#111713' }}>Stable Diffusion 1.5 (LoRA)</option>
                    <option value="SD-Turbo" style={{ background: '#111713' }}>SD-Turbo (Distillation)</option>
                    <option value="MobileDiffusion" style={{ background: '#111713' }}>MobileDiffusion (Edge)</option>
                    <option value="Multimodal Vision Adapter" style={{ background: '#111713' }}>Multimodal Vision Adapter</option>
                  </Select>
                </Box>

                <Box>
                  <Text fontSize="xs" color="#6B7B6D" mb={1.5} textTransform="uppercase">
                    Dataset
                  </Text>
                  <Select
                    value={selectedDataset}
                    onChange={(e) => setSelectedDataset(e.target.value)}
                    bg="#0F1A11"
                    color="#F4F7F0"
                    border="1px solid #2A3A2C"
                    borderRadius="10px"
                    size="sm"
                  >
                    <option value="Custom Portraits v3" style={{ background: '#111713' }}>Custom Portraits v3 (2.4k imgs)</option>
                    <option value="Anime Characters" style={{ background: '#111713' }}>Anime Characters (8.2k imgs)</option>
                    <option value="Product Shots" style={{ background: '#111713' }}>Product Shots (1.8k imgs)</option>
                    <option value="Architectural Renders" style={{ background: '#111713' }}>Architectural Renders (3.1k imgs)</option>
                  </Select>
                </Box>
              </Grid>

              <Grid templateColumns="1fr 1fr 1fr" gap={3} mb={4}>
                <Box>
                  <Text fontSize="xs" color="#6B7B6D" mb={1.5} textTransform="uppercase">
                    Batch Size
                  </Text>
                  <Select
                    value={batchSize}
                    onChange={(e) => setBatchSize(e.target.value)}
                    bg="#0F1A11"
                    color="#F4F7F0"
                    border="1px solid #2A3A2C"
                    borderRadius="10px"
                    size="sm"
                  >
                    <option value="4" style={{ background: '#111713' }}>4 (VRAM Safe)</option>
                    <option value="8" style={{ background: '#111713' }}>8 (Standard)</option>
                    <option value="16" style={{ background: '#111713' }}>16 (Optimal)</option>
                    <option value="32" style={{ background: '#111713' }}>32 (Cluster)</option>
                  </Select>
                </Box>

                <Box>
                  <Text fontSize="xs" color="#6B7B6D" mb={1.5} textTransform="uppercase">
                    Epochs
                  </Text>
                  <Select
                    value={epochs}
                    onChange={(e) => setEpochs(e.target.value)}
                    bg="#0F1A11"
                    color="#F4F7F0"
                    border="1px solid #2A3A2C"
                    borderRadius="10px"
                    size="sm"
                  >
                    <option value="25" style={{ background: '#111713' }}>25 Epochs</option>
                    <option value="50" style={{ background: '#111713' }}>50 Epochs</option>
                    <option value="100" style={{ background: '#111713' }}>100 Epochs</option>
                    <option value="200" style={{ background: '#111713' }}>200 Epochs</option>
                  </Select>
                </Box>

                <Box>
                  <Text fontSize="xs" color="#6B7B6D" mb={1.5} textTransform="uppercase">
                    Learning Rate
                  </Text>
                  <Select
                    value={learningRate}
                    onChange={(e) => setLearningRate(e.target.value)}
                    bg="#0F1A11"
                    color="#F4F7F0"
                    border="1px solid #2A3A2C"
                    borderRadius="10px"
                    size="sm"
                  >
                    <option value="1e-4" style={{ background: '#111713' }}>1e-4 (Fast)</option>
                    <option value="5e-5" style={{ background: '#111713' }}>5e-5 (Balanced)</option>
                    <option value="1e-5" style={{ background: '#111713' }}>1e-5 (Fine)</option>
                  </Select>
                </Box>
              </Grid>
            </ModalBody>

            <ModalFooter borderTop="1px solid #1A2A1C" py={3}>
              <Button size="sm" variant="ghost" color="#A5B1A7" mr={3} onClick={() => setIsModalOpen(false)}>
                Cancel
              </Button>
              <Button size="sm" bg="#B7FF35" color="#080B0A" fontWeight="bold" onClick={handleStartTraining}>
                Start Training Job
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </Box>
    </WorkspaceLayout>
  );
};

export default TrainingDatasets;
