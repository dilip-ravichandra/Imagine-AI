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
  Badge,
  Grid,
  GridItem,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  ModalFooter,
  Tooltip,
} from '@chakra-ui/react';
import {
  FiBookOpen,
  FiMic,
  FiRefreshCw,
  FiEdit3,
  FiDownload,
  FiVolume2,
  FiChevronLeft,
  FiChevronRight,
  FiPlus,
  FiTrash2,
  FiSliders,
  FiLayers,
} from 'react-icons/fi';
import WorkspaceLayout from '../components/WorkspaceLayout';
import InteractiveCanvasMask from '../components/InteractiveCanvasMask';

interface StoryScene {
  id: number;
  title: string;
  imagePrompt: string;
  imageUrl: string;
  narration: string;
  dialogue?: string;
  character: string;
}

const GENRES = [
  'Children Storybook (Ages 4-8)',
  'Youth Adventure (Ages 9-14)',
  'Comic Book / Graphic Novel',
  'Manga & Anime Style',
  'Sci-Fi Fantasy Epic',
];

const ART_STYLES = [
  'Pixar 3D Animation',
  'Classic Watercolor',
  'Modern Comic Strip',
  'Retro Manga Ink',
  'Vintage Children Illustration',
  'Oil Painting Fantasy',
];

const LANGUAGES = [
  { code: 'hi', name: 'Hindi (हिंदी)', sample: 'एक दयालु भालू जो जंगल के सारे जानवरों की मदद करता है और अपनी शहद की दुकान खोलता है' },
  { code: 'es', name: 'Spanish (Español)', sample: 'Un joven astrónomo que descubre un planeta hecho de cristal y música' },
  { code: 'fr', name: 'French (Français)', sample: 'Deux petits chats courageux qui partent à la recherche d\'un trésor secret' },
  { code: 'en', name: 'English', sample: 'A friendly little robot who rescues a lost kitten in a neon city and learns what family means' },
  { code: 'ja', name: 'Japanese (日本語)', sample: '雲の上に住むドラゴンの子どもと空飛ぶクジラの冒険物語' },
];

const INITIAL_SCENES: StoryScene[] = [
  {
    id: 1,
    title: 'Scene 1: The Waking City',
    imagePrompt: 'A friendly little brass robot named Bolt rolling through a gleaming sunlit futuristic city with solar trees, Pixar 3D style',
    imageUrl: 'https://picsum.photos/seed/story-scene1/600/400',
    narration: 'In a city made of sunlight and glass, lived a little robot named Bolt. Every morning, Bolt polished his silver gears and rolled out to explore the bustling avenues.',
    dialogue: 'Bolt: "Another beautiful day for new discoveries!"',
    character: 'Bolt the Robot',
  },
  {
    id: 2,
    title: 'Scene 2: A Tiny Surprise',
    imagePrompt: 'Bolt peering behind a green recycle container and discovering a small shivering orange kitten, soft cinematic lighting',
    imageUrl: 'https://picsum.photos/seed/story-scene2/600/400',
    narration: 'Behind a solar charging post, Bolt heard a soft sound: "Meow!" Cuddled inside an old cardboard box was a tiny calico kitten, looking up with curious emerald eyes.',
    dialogue: 'Bolt: "Beep! You have fur and no batteries... are you lost?"',
    character: 'Bolt & Spark',
  },
  {
    id: 3,
    title: 'Scene 3: The Rain & Shelter',
    imagePrompt: 'Bolt holding an umbrella over the kitten as colorful neon rain falls on the futuristic sidewalk, warm heart-warming lighting',
    imageUrl: 'https://picsum.photos/seed/story-scene3/600/400',
    narration: 'When neon raindrops began to sprinkle from the clouds, Bolt gently scooped the kitten into his arms and popped open his built-in umbrella dome.',
    dialogue: 'Spark: "*Purrrr...*"',
    character: 'Bolt & Spark',
  },
  {
    id: 4,
    title: 'Scene 4: True Friendship',
    imagePrompt: 'Bolt and the kitten sitting together on a high rooftop terrace watching shooting stars and glowing auroras above the city',
    imageUrl: 'https://picsum.photos/seed/story-scene4/600/400',
    narration: 'Together on the high rooftop, Bolt and his new friend Spark watched the stars shimmer. Bolt learned that the greatest circuits in the universe are the ones that feel friendship.',
    dialogue: 'Bolt: "You and me, Spark. Best friends in the whole galaxy."',
    character: 'Bolt & Spark',
  },
];

const StoryBookStudio: React.FC = () => {
  const [viewMode, setViewMode] = useState<'book' | 'comic'>('comic');
  const [genre, setGenre] = useState(GENRES[0]);
  const [artStyle, setArtStyle] = useState(ART_STYLES[0]);
  const [storyTitle, setStoryTitle] = useState('The Little Robot and His Kitten Friend');
  const [storyIdea, setStoryIdea] = useState(
    'A friendly little brass robot named Bolt discovers a lost kitten in a futuristic eco-city, protecting it from the rain and learning the true meaning of friendship.'
  );
  const [scenes, setScenes] = useState<StoryScene[]>(INITIAL_SCENES);
  const [activeBookIndex, setActiveBookIndex] = useState(0);
  const [isGeneratingStory, setIsGeneratingStory] = useState(false);

  // Selective Scene Recreator Modal
  const [isRecreating, setIsRecreating] = useState(false);
  const [selectedScene, setSelectedScene] = useState<StoryScene | null>(null);
  const [recreatePromptChange, setRecreatePromptChange] = useState('');
  const [isRegeneratingPanel, setIsRegeneratingPanel] = useState(false);

  // Voice Translation Modal
  const [isVoiceModalOpen, setIsVoiceModalOpen] = useState(false);
  const [selectedLang, setSelectedLang] = useState(LANGUAGES[0]);
  const [isRecording, setIsRecording] = useState(false);
  const [spokenStory, setSpokenStory] = useState(LANGUAGES[0].sample);
  const [translatedStoryPlot, setTranslatedStoryPlot] = useState(
    'A kind-hearted bear who helps all forest creatures with his handmade honey bakery, teaching teamwork and generosity.'
  );

  // Text to speech active state
  const [readingSceneId, setReadingSceneId] = useState<number | null>(null);

  // Handle Full Story Generation
  const handleGenerateStory = () => {
    setIsGeneratingStory(true);
    setTimeout(() => {
      const generated: StoryScene[] = [
        {
          id: 1,
          title: 'Scene 1: The Beginning',
          imagePrompt: `${storyIdea} - Opening scene, ${artStyle}, high detail`,
          imageUrl: `https://picsum.photos/seed/storygen1${Date.now()}/600/400`,
          narration: `Once upon a time in a vibrant world, the story begins: ${storyIdea.slice(0, 90)}...`,
          dialogue: 'Hero: "Our journey starts today!"',
          character: 'Main Character',
        },
        {
          id: 2,
          title: 'Scene 2: The Adventure Unfolds',
          imagePrompt: `${storyIdea} - Mid journey conflict or mystery, ${artStyle}`,
          imageUrl: `https://picsum.photos/seed/storygen2${Date.now()}/600/400`,
          narration: 'As obstacles appeared along the path, unexpected companions joined hands to solve the mystery.',
          dialogue: 'Companion: "Look ahead, there is light beyond the misty horizon!"',
          character: 'Companion',
        },
        {
          id: 3,
          title: 'Scene 3: The Climax',
          imagePrompt: `${storyIdea} - Climax moment with emotional connection, ${artStyle}`,
          imageUrl: `https://picsum.photos/seed/storygen3${Date.now()}/600/400`,
          narration: 'Facing the greatest challenge of all, kindness and courage turned darkness into radiant joy.',
          dialogue: 'All: "Together we can accomplish anything!"',
          character: 'Heroes Together',
        },
        {
          id: 4,
          title: 'Scene 4: The Happy Ending',
          imagePrompt: `${storyIdea} - Warm celebration sunset scene, ${artStyle}`,
          imageUrl: `https://picsum.photos/seed/storygen4${Date.now()}/600/400`,
          narration: 'And from that memorable day forward, joy echoed across the kingdom. The end.',
          dialogue: 'Narrator: "A journey remembered for generations."',
          character: 'Happy Ensemble',
        },
      ];
      setScenes(generated);
      setIsGeneratingStory(false);
    }, 2000);
  };

  // Open Selective Recreator
  const handleOpenRecreate = (scene: StoryScene) => {
    setSelectedScene(scene);
    setRecreatePromptChange('Make the lighting dramatic golden hour, with playful sparks floating around');
    setIsRecreating(true);
  };

  // Apply Selective Recreation to just that one scene
  const handleApplySceneRecreation = () => {
    if (!selectedScene) return;
    setIsRegeneratingPanel(true);

    setTimeout(() => {
      setScenes((prev) =>
        prev.map((s) =>
          s.id === selectedScene.id
            ? {
                ...s,
                imageUrl: `https://picsum.photos/seed/recreated${Date.now()}/600/400`,
                imagePrompt: `${s.imagePrompt} [Recreated: ${recreatePromptChange}]`,
              }
            : s
        )
      );
      setIsRegeneratingPanel(false);
      setIsRecreating(false);
    }, 1500);
  };

  // Voice Dictation handler
  const handleToggleVoice = () => {
    if (!isRecording) {
      setIsRecording(true);
      setTimeout(() => {
        setIsRecording(false);
        setSpokenStory(selectedLang.sample);
        setTranslatedStoryPlot(
          `An enchanting illustrated tale about: ${selectedLang.sample}, filled with whimsical wonder, teamwork, and colorful scenes.`
        );
      }, 2000);
    } else {
      setIsRecording(false);
    }
  };

  const handleApplyVoiceStory = () => {
    setStoryIdea(translatedStoryPlot);
    setIsVoiceModalOpen(false);
  };

  // Read Aloud Simulation
  const handleReadAloud = (sceneId: number) => {
    setReadingSceneId(sceneId);
    setTimeout(() => {
      setReadingSceneId(null);
    }, 3000);
  };

  return (
    <WorkspaceLayout>
      <Box p={{ base: 4, md: 6 }} minH="100vh" bg="#080B0A">
        {/* Top Header */}
        <Box bg="#111713" border="1px solid #2A3A2C" borderRadius="16px" p={5} mb={6}>
          <Flex direction={{ base: 'column', lg: 'row' }} justify="space-between" align={{ base: 'flex-start', lg: 'center' }} gap={4}>
            <Flex align="center" gap={3}>
              <Box
                w="40px"
                h="40px"
                borderRadius="10px"
                bg="#B7FF35"
                display="flex"
                alignItems="center"
                justifyContent="center"
                fontSize="20px"
                color="#080B0A"
              >
                📖
              </Box>
              <Box>
                <Flex align="center" gap={2}>
                  <Heading size="md" color="#F4F7F0" fontWeight="700">
                    Storybook & Comic Studio
                  </Heading>
                  <Badge bg="rgba(183, 255, 53, 0.15)" color="#B7FF35" px={2} py={0.5} borderRadius="full" fontSize="10px">
                    Multi-Scene Creator
                  </Badge>
                </Flex>
                <Text color="#A5B1A7" fontSize="xs">
                  Create illustrated storybooks and comics for kids & adults — with voice dictation & selective panel recreator
                </Text>
              </Box>
            </Flex>

            {/* View Mode Toggle: Comic Strip vs Storybook */}
            <Flex align="center" gap={3}>
              <Flex bg="#0F1A11" p={1} borderRadius="10px" border="1px solid #2A3A2C">
                <Button
                  size="xs"
                  borderRadius="8px"
                  bg={viewMode === 'comic' ? '#B7FF35' : 'transparent'}
                  color={viewMode === 'comic' ? '#080B0A' : '#A5B1A7'}
                  fontWeight="bold"
                  onClick={() => setViewMode('comic')}
                  leftIcon={<Text fontSize="12px">💬</Text>}
                >
                  Comic Strip Panels
                </Button>
                <Button
                  size="xs"
                  borderRadius="8px"
                  bg={viewMode === 'book' ? '#B7FF35' : 'transparent'}
                  color={viewMode === 'book' ? '#080B0A' : '#A5B1A7'}
                  fontWeight="bold"
                  onClick={() => setViewMode('book')}
                  leftIcon={<Text fontSize="12px">📖</Text>}
                >
                  Storybook Reader
                </Button>
              </Flex>

              <Button
                size="sm"
                variant="outline"
                borderColor="#2A3A2C"
                color="#A5B1A7"
                _hover={{ color: '#B7FF35', borderColor: '#B7FF35' }}
                leftIcon={<FiDownload />}
              >
                Export PDF
              </Button>
            </Flex>
          </Flex>

          {/* Story Prompt & Controls Bar */}
          <Box mt={5} pt={4} borderTop="1px solid #1A2A1C">
            <Grid templateColumns={{ base: '1fr', lg: '3fr 1fr 1fr auto' }} gap={3} align="flex-end">
              <Box>
                <Flex justify="space-between" align="center" mb={1.5}>
                  <Text fontSize="xs" color="#A5B1A7" fontWeight="600">
                    Story Concept or Plotline
                  </Text>
                  <Button
                    size="xs"
                    variant="link"
                    color="#B7FF35"
                    leftIcon={<FiMic />}
                    onClick={() => setIsVoiceModalOpen(true)}
                  >
                    Dictate in any language
                  </Button>
                </Flex>
                <Input
                  value={storyIdea}
                  onChange={(e) => setStoryIdea(e.target.value)}
                  placeholder="Describe your story idea or characters..."
                  bg="#0F1A11"
                  color="#F4F7F0"
                  border="1px solid #2A3A2C"
                  borderRadius="10px"
                  size="sm"
                  _focus={{ borderColor: '#B7FF35' }}
                />
              </Box>

              <Box>
                <Text fontSize="xs" color="#6B7B6D" mb={1.5}>Genre / Audience</Text>
                <Select
                  value={genre}
                  onChange={(e) => setGenre(e.target.value)}
                  bg="#0F1A11"
                  color="#F4F7F0"
                  border="1px solid #2A3A2C"
                  borderRadius="10px"
                  size="sm"
                >
                  {GENRES.map((g) => (
                    <option key={g} value={g} style={{ background: '#111713' }}>
                      {g}
                    </option>
                  ))}
                </Select>
              </Box>

              <Box>
                <Text fontSize="xs" color="#6B7B6D" mb={1.5}>Art Style</Text>
                <Select
                  value={artStyle}
                  onChange={(e) => setArtStyle(e.target.value)}
                  bg="#0F1A11"
                  color="#F4F7F0"
                  border="1px solid #2A3A2C"
                  borderRadius="10px"
                  size="sm"
                >
                  {ART_STYLES.map((a) => (
                    <option key={a} value={a} style={{ background: '#111713' }}>
                      {a}
                    </option>
                  ))}
                </Select>
              </Box>

              <Button
                bg="#B7FF35"
                color="#080B0A"
                fontWeight="700"
                size="sm"
                h="36px"
                px={6}
                borderRadius="10px"
                _hover={{ bg: '#8DDB39', transform: 'translateY(-1px)' }}
                onClick={handleGenerateStory}
                isLoading={isGeneratingStory}
                leftIcon={<Text>✨</Text>}
              >
                Generate Scenes
              </Button>
            </Grid>
          </Box>
        </Box>

        {/* VIEW 1: COMIC STRIP PANELS VIEW */}
        {viewMode === 'comic' && (
          <Grid templateColumns={{ base: '1fr', md: 'repeat(2, 1fr)' }} gap={6}>
            {scenes.map((scene, idx) => (
              <GridItem key={scene.id}>
                <Box
                  bg="#111713"
                  border="1px solid #2A3A2C"
                  borderRadius="16px"
                  overflow="hidden"
                  boxShadow="0 8px 30px rgba(0,0,0,0.5)"
                  transition="all 0.25s"
                  _hover={{ borderColor: '#3A4A3C', transform: 'translateY(-2px)' }}
                >
                  {/* Panel Header */}
                  <Flex px={4} py={3} justify="space-between" align="center" bg="#0D120E" borderBottom="1px solid #1A2A1C">
                    <Flex align="center" gap={2}>
                      <Badge bg="#182019" color="#B7FF35" px={2} py={0.5} borderRadius="6px" fontSize="11px">
                        Panel {idx + 1}
                      </Badge>
                      <Text fontSize="xs" fontWeight="bold" color="#F4F7F0">
                        {scene.title}
                      </Text>
                    </Flex>
                    <HStack spacing={1}>
                      {/* Selective Recreate Button */}
                      <Tooltip label="Selective recreation: re-generate only this panel">
                        <Button
                          size="xs"
                          variant="ghost"
                          color="#B7FF35"
                          _hover={{ bg: '#182019' }}
                          leftIcon={<FiRefreshCw size={12} />}
                          onClick={() => handleOpenRecreate(scene)}
                        >
                          Recreate Panel
                        </Button>
                      </Tooltip>

                      {/* Read Aloud Narration */}
                      <Tooltip label="Read dialogue aloud">
                        <IconButton
                          aria-label="Read aloud"
                          icon={<FiVolume2 size={13} />}
                          size="xs"
                          variant="ghost"
                          color={readingSceneId === scene.id ? '#B7FF35' : '#A5B1A7'}
                          _hover={{ color: '#F4F7F0', bg: '#182019' }}
                          onClick={() => handleReadAloud(scene.id)}
                        />
                      </Tooltip>
                    </HStack>
                  </Flex>

                  {/* Panel Image */}
                  <Box position="relative" overflow="hidden" bg="#080B0A">
                    <Image
                      src={scene.imageUrl}
                      alt={scene.title}
                      w="100%"
                      h="260px"
                      objectFit="cover"
                      transition="transform 0.4s ease"
                    />

                    {/* Comic Dialogue Bubble overlay */}
                    {scene.dialogue && (
                      <Box
                        position="absolute"
                        bottom={3}
                        left={3}
                        right={3}
                        bg="rgba(17, 23, 19, 0.88)"
                        border="1px solid #B7FF35"
                        borderRadius="12px"
                        p={2.5}
                        backdropFilter="blur(8px)"
                        boxShadow="0 4px 16px rgba(0,0,0,0.6)"
                      >
                        <Text fontSize="xs" color="#F4F7F0" fontWeight="600" fontStyle="italic">
                          💬 {scene.dialogue}
                        </Text>
                      </Box>
                    )}
                  </Box>

                  {/* Panel Narration */}
                  <Box p={4}>
                    <Text fontSize="xs" color="#A5B1A7" lineHeight="1.6">
                      {scene.narration}
                    </Text>
                    <Flex justify="space-between" align="center" mt={3} pt={2} borderTop="1px solid #1A2A1C">
                      <Text fontSize="10px" color="#6B7B6D">
                        Character: <span style={{ color: '#F4F7F0' }}>{scene.character}</span>
                      </Text>
                      <Text fontSize="10px" color="#8DDB39">
                        Consistent Model Style
                      </Text>
                    </Flex>
                  </Box>
                </Box>
              </GridItem>
            ))}
          </Grid>
        )}

        {/* VIEW 2: STORYBOOK READER MODE */}
        {viewMode === 'book' && scenes.length > 0 && (
          <Box maxW="880px" mx="auto" my={4}>
            <Box
              bg="#111713"
              border="2px solid #2A3A2C"
              borderRadius="24px"
              overflow="hidden"
              boxShadow="0 16px 64px rgba(0,0,0,0.8)"
            >
              <Grid templateColumns={{ base: '1fr', md: '1fr 1fr' }}>
                {/* Left Page: Artwork */}
                <Box bg="#080B0A" p={6} display="flex" alignItems="center" justifyContent="center">
                  <Image
                    src={scenes[activeBookIndex].imageUrl}
                    alt={scenes[activeBookIndex].title}
                    borderRadius="16px"
                    w="100%"
                    maxH="400px"
                    objectFit="cover"
                    border="1px solid #2A3A2C"
                  />
                </Box>

                {/* Right Page: Narrative & Dialogue */}
                <Flex direction="column" justify="space-between" p={8} bg="#0D120E">
                  <Box>
                    <Flex justify="space-between" align="center" mb={4}>
                      <Badge bg="rgba(183,255,53,0.15)" color="#B7FF35" px={3} py={1} borderRadius="full" fontSize="xs">
                        Page {activeBookIndex + 1} of {scenes.length}
                      </Badge>
                      <Button
                        size="xs"
                        variant="ghost"
                        color="#B7FF35"
                        leftIcon={<FiRefreshCw size={11} />}
                        onClick={() => handleOpenRecreate(scenes[activeBookIndex])}
                      >
                        Recreate Page
                      </Button>
                    </Flex>

                    <Heading size="md" color="#F4F7F0" mb={4}>
                      {scenes[activeBookIndex].title}
                    </Heading>

                    <Text fontSize="sm" color="#A5B1A7" lineHeight="1.8" mb={6}>
                      {scenes[activeBookIndex].narration}
                    </Text>

                    {scenes[activeBookIndex].dialogue && (
                      <Box bg="#111713" borderLeft="3px solid #B7FF35" p={3} borderRadius="8px" mb={4}>
                        <Text fontSize="xs" color="#F4F7F0" fontWeight="600">
                          {scenes[activeBookIndex].dialogue}
                        </Text>
                      </Box>
                    )}
                  </Box>

                  {/* Page Navigation */}
                  <Flex justify="space-between" align="center" pt={4} borderTop="1px solid #1A2A1C">
                    <Button
                      size="sm"
                      variant="ghost"
                      color="#A5B1A7"
                      isDisabled={activeBookIndex === 0}
                      onClick={() => setActiveBookIndex((prev) => Math.max(0, prev - 1))}
                      leftIcon={<FiChevronLeft />}
                    >
                      Previous
                    </Button>

                    <IconButton
                      aria-label="Read aloud"
                      icon={<FiVolume2 />}
                      size="sm"
                      bg="#182019"
                      color="#B7FF35"
                      borderRadius="full"
                      onClick={() => handleReadAloud(scenes[activeBookIndex].id)}
                    />

                    <Button
                      size="sm"
                      bg="#B7FF35"
                      color="#080B0A"
                      fontWeight="bold"
                      isDisabled={activeBookIndex === scenes.length - 1}
                      onClick={() => setActiveBookIndex((prev) => Math.min(scenes.length - 1, prev + 1))}
                      rightIcon={<FiChevronRight />}
                    >
                      Next
                    </Button>
                  </Flex>
                </Flex>
              </Grid>
            </Box>
          </Box>
        )}

        {/* SELECTIVE PANEL RECREATOR MODAL WITH CANVAS CIRCLING */}
        <Modal isOpen={isRecreating} onClose={() => setIsRecreating(false)} isCentered size="2xl">
          <ModalOverlay bg="rgba(0,0,0,0.88)" backdropFilter="blur(8px)" />
          <ModalContent bg="#111713" border="1px solid #2A3A2C" borderRadius="20px" color="#F4F7F0" maxW="700px">
            <ModalHeader borderBottom="1px solid #1A2A1C" py={4}>
              <Flex align="center" gap={2}>
                <Box w="28px" h="28px" borderRadius="full" bg="#B7FF35" display="flex" alignItems="center" justifyContent="center" color="#080B0A" fontSize="14px">
                  ⭕
                </Box>
                <Box>
                  <Text fontSize="md" fontWeight="bold">
                    Selective Panel Recreate — Circle Region
                  </Text>
                  <Text fontSize="xs" color="#A5B1A7" fontWeight="normal">
                    Circle or brush the exact part of the comic panel you want to alter
                  </Text>
                </Box>
              </Flex>
            </ModalHeader>
            <ModalCloseButton color="#A5B1A7" />

            <ModalBody py={4}>
              {selectedScene && (
                <Box mb={4}>
                  <InteractiveCanvasMask imageUrl={selectedScene.imageUrl} />
                </Box>
              )}

              <Box mb={3}>
                <Text fontSize="xs" color="#A5B1A7" fontWeight="600" mb={1.5} textTransform="uppercase">
                  What should appear in the circled area?
                </Text>
                <Input
                  value={recreatePromptChange}
                  onChange={(e) => setRecreatePromptChange(e.target.value)}
                  placeholder="e.g. Change expression to joyful laughter, add rainbow sparkles"
                  bg="#0F1A11"
                  color="#F4F7F0"
                  border="1px solid #2A3A2C"
                  borderRadius="10px"
                  size="sm"
                  _focus={{ borderColor: '#B7FF35' }}
                />
              </Box>
            </ModalBody>

            <ModalFooter borderTop="1px solid #1A2A1C" py={3}>
              <Button size="sm" variant="ghost" color="#A5B1A7" mr={3} onClick={() => setIsRecreating(false)}>
                Cancel
              </Button>
              <Button
                size="sm"
                bg="#B7FF35"
                color="#080B0A"
                fontWeight="bold"
                onClick={handleApplySceneRecreation}
                isLoading={isRegeneratingPanel}
                leftIcon={<Text>✨</Text>}
              >
                Recreate Circled Area
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>

        {/* VOICE DICTATION & TRANSLATION MODAL */}
        <Modal isOpen={isVoiceModalOpen} onClose={() => setIsVoiceModalOpen(false)} isCentered size="lg">
          <ModalOverlay bg="rgba(0,0,0,0.85)" backdropFilter="blur(6px)" />
          <ModalContent bg="#111713" border="1px solid #2A3A2C" borderRadius="18px" color="#F4F7F0">
            <ModalHeader borderBottom="1px solid #1A2A1C" py={4}>
              <Flex align="center" gap={2}>
                <Box w="28px" h="28px" borderRadius="full" bg="#B7FF35" display="flex" alignItems="center" justifyContent="center" color="#080B0A" fontSize="14px">
                  🎤
                </Box>
                <Text fontSize="md" fontWeight="bold">
                  Story Voice Dictator & Translator
                </Text>
              </Flex>
            </ModalHeader>
            <ModalCloseButton color="#A5B1A7" />

            <ModalBody py={5}>
              <Text fontSize="xs" color="#A5B1A7" mb={4}>
                Tell your story verbally in your mother tongue! The voice translator converts it into a multi-scene plotline ready for generation.
              </Text>

              <Box mb={4}>
                <Text fontSize="xs" color="#6B7B6D" mb={1.5} textTransform="uppercase">
                  Select Speaking Language
                </Text>
                <Select
                  value={selectedLang.code}
                  onChange={(e) => {
                    const l = LANGUAGES.find((item) => item.code === e.target.value) || LANGUAGES[0];
                    setSelectedLang(l);
                    setSpokenStory(l.sample);
                  }}
                  bg="#0F1A11"
                  color="#F4F7F0"
                  border="1px solid #2A3A2C"
                  borderRadius="10px"
                  size="sm"
                >
                  {LANGUAGES.map((l) => (
                    <option key={l.code} value={l.code} style={{ background: '#111713' }}>
                      {l.name}
                    </option>
                  ))}
                </Select>
              </Box>

              <Flex direction="column" align="center" py={4}>
                <Box
                  w="70px"
                  h="70px"
                  borderRadius="full"
                  bg={isRecording ? '#FF4444' : '#182019'}
                  border="2px solid"
                  borderColor={isRecording ? '#FF4444' : '#B7FF35'}
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                  cursor="pointer"
                  onClick={handleToggleVoice}
                  boxShadow={isRecording ? '0 0 25px rgba(255,68,68,0.5)' : '0 0 20px rgba(183,255,53,0.3)'}
                >
                  <FiMic size={28} color={isRecording ? '#F4F7F0' : '#B7FF35'} />
                </Box>
                <Text fontSize="xs" color={isRecording ? '#FF4444' : '#B7FF35'} fontWeight="600" mt={2}>
                  {isRecording ? 'Recording your voice...' : 'Tap to narrate your story'}
                </Text>
              </Flex>

              <Box bg="#0D120E" p={4} borderRadius="12px" border="1px solid #2A3A2C">
                <Text fontSize="10px" color="#6B7B6D" textTransform="uppercase" fontWeight="bold">
                  Transcribed ({selectedLang.name})
                </Text>
                <Text fontSize="xs" color="#F4F7F0" mt={1}>
                  "{spokenStory}"
                </Text>
                <Box h="1px" bg="#1A2A1C" my={2.5} />
                <Text fontSize="10px" color="#8DDB39" textTransform="uppercase" fontWeight="bold">
                  ✨ Translated Story Concept
                </Text>
                <Text fontSize="xs" color="#B7FF35" mt={1}>
                  {translatedStoryPlot}
                </Text>
              </Box>
            </ModalBody>

            <ModalFooter borderTop="1px solid #1A2A1C" py={3}>
              <Button size="sm" variant="ghost" color="#A5B1A7" mr={3} onClick={() => setIsVoiceModalOpen(false)}>
                Cancel
              </Button>
              <Button size="sm" bg="#B7FF35" color="#080B0A" fontWeight="bold" onClick={handleApplyVoiceStory}>
                Use As Story Plot
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </Box>
    </WorkspaceLayout>
  );
};

export default StoryBookStudio;
