import React, { useState, useRef } from 'react';
import {
  Box,
  Flex,
  Text,
  Heading,
  Textarea,
  Input,
  Button,
  Select,
  Image,
  Badge,
  HStack,
  VStack,
  IconButton,
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
  FiMic,
  FiPaperclip,
  FiSend,
  FiRefreshCw,
  FiDownload,
  FiEdit,
  FiMessageSquare,
  FiZap,
  FiX,
  FiVolume2,
  FiSliders,
  FiTrash2,
  FiCheck,
} from 'react-icons/fi';
import WorkspaceLayout from '../components/WorkspaceLayout';
import InteractiveCanvasMask from '../components/InteractiveCanvasMask';

interface GenerationItem {
  id: string;
  timestamp: string;
  prompt: string;
  enhancedPrompt?: string;
  style: string;
  model: string;
  aspect: string;
  imageUrl: string;
  referenceImage?: string;
  voiceLanguage?: string;
  originalVoiceText?: string;
  isRecreation?: boolean;
  parentImageId?: string;
  recreationNote?: string;
}

const STYLE_OPTIONS = [
  'Photorealistic',
  'Cinematic 3D',
  'Anime & Manga',
  'Comic Book',
  'Fantasy Art',
  'Cyberpunk',
  'Watercolor',
  'Retro Pixel',
];

const MODEL_OPTIONS = [
  'SD-Turbo (Realtime 0.8s)',
  'Stable Diffusion 1.5',
  'MobileDiffusion (Efficient)',
  'BK-SDM-Tiny',
  'Multimodal Vision-Diffuser',
];

const ASPECT_OPTIONS = ['1:1 Square', '16:9 Landscape', '9:16 Portrait', '4:3 Standard'];
const QUALITY_OPTIONS = ['Quick (1-step)', 'Balanced (4-step)', 'Best (High Res)'];

const LANGUAGES = [
  { code: 'hi', name: 'Hindi (हिंदी)', sample: 'एक जादुई जंगल जिसमें चमकते हुए पेड़ और नीले फूल हैं' },
  { code: 'es', name: 'Spanish (Español)', sample: 'Una ciudad futurista con rascacielos flotantes al atardecer' },
  { code: 'fr', name: 'French (Français)', sample: 'Un petit robot mignon qui lit un livre sous les étoiles' },
  { code: 'de', name: 'German (Deutsch)', sample: 'Ein alter Drache der auf einer Bergspitze im Schnee schläft' },
  { code: 'ja', name: 'Japanese (日本語)', sample: '桜の花びらが舞うサイバーパンクの夜の通り' },
  { code: 'ta', name: 'Tamil (தமிழ்)', sample: 'வானத்தில் பறக்கும் தங்க ரதம் மற்றும் மேகங்கள்' },
  { code: 'en', name: 'English (Voice Prompt)', sample: 'A friendly dragon making pastries in a rustic bakery' },
];

const INITIAL_GENERATIONS: GenerationItem[] = [
  {
    id: 'gen-1',
    timestamp: 'Just now',
    prompt: 'A futuristic city with green energy, at sunset, cinematic, ultra realistic',
    enhancedPrompt: 'A breathtaking futuristic metropolis powered by glowing emerald bioluminescent energy towers, majestic crystalline skybridges, golden sunset reflections, 8k resolution, volumetric fog, octane render.',
    style: 'Photorealistic',
    model: 'SD-Turbo (Realtime 0.8s)',
    aspect: '16:9 Landscape',
    imageUrl: 'https://picsum.photos/seed/futurecity99/900/500',
    voiceLanguage: 'Hindi (हिंदी)',
    originalVoiceText: 'एक भविष्य का शहर जिसमें हरी ऊर्जा और सूर्यास्त का दृश्य हो',
  },
  {
    id: 'gen-2',
    timestamp: '2 mins ago',
    prompt: 'A cute metallic steampunk robot petting a curious fluffy kitten in a flower garden',
    enhancedPrompt: 'Detailed Pixar-style 3D render of a gentle brass steampunk automaton with glowing amber optical eyes softly cuddling a miniature calico kitten in an English meadow blooming with lavender, warm golden hour backlighting, cinematic depth of field.',
    style: 'Cinematic 3D',
    model: 'SD-Turbo (Realtime 0.8s)',
    aspect: '1:1 Square',
    imageUrl: 'https://picsum.photos/seed/robotcat77/600/600',
  },
];

const CreateStudio: React.FC = () => {
  const [generations, setGenerations] = useState<GenerationItem[]>(INITIAL_GENERATIONS);
  const [prompt, setPrompt] = useState('');
  const [style, setStyle] = useState('Photorealistic');
  const [model, setModel] = useState('SD-Turbo (Realtime 0.8s)');
  const [aspect, setAspect] = useState('16:9 Landscape');
  const [quality, setQuality] = useState('Balanced (4-step)');
  const [isGenerating, setIsGenerating] = useState(false);
  const [attachedImage, setAttachedImage] = useState<string | null>(null);

  // Voice Translation Modal State
  const [isVoiceOpen, setIsVoiceOpen] = useState(false);
  const [voiceLang, setVoiceLang] = useState(LANGUAGES[0]);
  const [isRecording, setIsRecording] = useState(false);
  const [spokenText, setSpokenText] = useState(LANGUAGES[0].sample);
  const [translatedPrompt, setTranslatedPrompt] = useState(
    'A magical forest with glowing bioluminescent trees, mystical floating blue orchids, ethereal moonlight rays, ultra detailed'
  );

  // Selective Recreation Modal State
  const [isRecreationOpen, setIsRecreationOpen] = useState(false);
  const [selectedTargetImage, setSelectedTargetImage] = useState<GenerationItem | null>(null);
  const [recreationInstruction, setRecreationInstruction] = useState('');
  const [recreationRegion, setRecreationRegion] = useState('Circled Area');
  const [hasMaskSelected, setHasMaskSelected] = useState(false);
  const [maskDataUrl, setMaskDataUrl] = useState<string | null>(null);

  // Question / Vision Inspector state
  const [activeQuestionId, setActiveQuestionId] = useState<string | null>(null);
  const [imageAnswer, setImageAnswer] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle Voice Recording Simulation
  const handleToggleRecord = () => {
    if (!isRecording) {
      setIsRecording(true);
      setTimeout(() => {
        setIsRecording(false);
        setSpokenText(voiceLang.sample);
        // Translate and enhance
        const translations: Record<string, string> = {
          hi: 'A mystical ancient enchanted forest with towering glowing green trees and luminescent blue blossoms, cinematic volumetric lighting, 8k masterpiece',
          es: 'A sprawling futuristic skyline with floating iridescent skyscrapers during a crimson sunset, hyper-detailed architectural render',
          fr: 'An adorable miniature robot with vintage brass gears reading an ancient leather book under starry cosmos, soft warm storybook illustration',
          de: 'A colossal primordial dragon slumbering peacefully upon a snowy mountain crest during an aurora borealis, dark fantasy oil painting',
          ja: 'A nocturnal cyberpunk alley drenched in neon reflections with floating pink sakura cherry blossom petals, anime cinematic still',
          ta: 'A majestic celestial golden chariot soaring through celestial clouds with lightning trails, epic mythological digital concept art',
          en: 'A warm, whimsical friendly dragon delicately baking croissants inside an old French village bakery, charming 3D storybook character',
        };
        setTranslatedPrompt(translations[voiceLang.code] || `A stunning rendition of: ${spokenText}, 8k cinematic masterpiece`);
      }, 2000);
    } else {
      setIsRecording(false);
    }
  };

  const handleApplyVoicePrompt = () => {
    setPrompt(translatedPrompt);
    setIsVoiceOpen(false);
  };

  // Enhance prompt function
  const handleEnhancePrompt = () => {
    if (!prompt.trim()) {
      setPrompt('A futuristic eco-friendly floating city with waterfalls, solar sail architecture, golden hour cinematic lighting, 8k octane render, masterpiece');
      return;
    }
    setPrompt(
      (prev) =>
        `${prev}, cinematic composition, hyper-detailed textures, volumetric atmospheric lighting, 8k resolution, ray-traced reflections, trending on ArtStation, masterpiece.`
    );
  };

  // Image upload
  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setAttachedImage(url);
    }
  };

  // Trigger Generation
  const handleGenerate = () => {
    if (!prompt.trim() && !attachedImage) return;

    setIsGenerating(true);
    const newId = `gen-${Date.now()}`;
    const newPrompt = prompt.trim() || 'Visual remix from uploaded reference image';

    setTimeout(() => {
      const newGen: GenerationItem = {
        id: newId,
        timestamp: 'Just now',
        prompt: newPrompt,
        style,
        model,
        aspect,
        imageUrl: `https://picsum.photos/seed/${Date.now()}/${aspect.includes('16:9') ? '900/500' : '600/600'}`,
        referenceImage: attachedImage || undefined,
        voiceLanguage: spokenText && prompt.includes(translatedPrompt) ? voiceLang.name : undefined,
        originalVoiceText: spokenText && prompt.includes(translatedPrompt) ? spokenText : undefined,
      };

      setGenerations((prev) => [newGen, ...prev]);
      setIsGenerating(false);
      setPrompt('');
      setAttachedImage(null);
    }, 1500);
  };

  // Trigger Selective Recreate
  const handleOpenSelectiveRecreate = (item: GenerationItem) => {
    setSelectedTargetImage(item);
    setRecreationInstruction('Change the sky to deep violet with shooting stars and neon aurora');
    setIsRecreationOpen(true);
  };

  const handleApplySelectiveRecreation = () => {
    if (!selectedTargetImage) return;

    setIsGenerating(true);
    setIsRecreationOpen(false);

    setTimeout(() => {
      const recreated: GenerationItem = {
        id: `recreate-${Date.now()}`,
        timestamp: 'Just now (Recreated)',
        prompt: `${selectedTargetImage.prompt} [Modified: ${recreationInstruction} on ${recreationRegion}]`,
        style: selectedTargetImage.style,
        model: selectedTargetImage.model,
        aspect: selectedTargetImage.aspect,
        imageUrl: `https://picsum.photos/seed/recreate${Date.now()}/900/500`,
        isRecreation: true,
        parentImageId: selectedTargetImage.id,
        recreationNote: `Selective Inpaint on ${recreationRegion}: "${recreationInstruction}"`,
      };

      setGenerations((prev) => [recreated, ...prev]);
      setIsGenerating(false);
    }, 1500);
  };

  // Ask Image Questions
  const handleAskAboutImage = (id: string) => {
    setActiveQuestionId(id);
    setImageAnswer(
      'Vision Model Analysis: The composition features strong diagonal balance with focal points along the rule of thirds. Lighting has high warm-cool contrast with specular highlights. The focal subject has fine mechanical detailing and warm emotional expression.'
    );
  };

  return (
    <WorkspaceLayout>
      <Box p={{ base: 4, md: 6 }} minH="100vh" bg="#080B0A" display="flex" flexDir="column">
        {/* Top Header & Studio Controls Bar */}
        <Box
          bg="#111713"
          border="1px solid #2A3A2C"
          borderRadius="16px"
          p={4}
          mb={6}
          boxShadow="0 4px 20px rgba(0,0,0,0.5)"
        >
          <Flex
            direction={{ base: 'column', lg: 'row' }}
            justify="space-between"
            align={{ base: 'flex-start', lg: 'center' }}
            gap={4}
          >
            <Flex align="center" gap={3}>
              <Box
                w="38px"
                h="38px"
                borderRadius="10px"
                bg="#B7FF35"
                display="flex"
                alignItems="center"
                justifyContent="center"
                fontSize="18px"
                fontWeight="bold"
                color="#080B0A"
              >
                🎨
              </Box>
              <Box>
                <Flex align="center" gap={2}>
                  <Heading size="md" color="#F4F7F0" fontWeight="700">
                    Create Studio
                  </Heading>
                  <Badge bg="rgba(183, 255, 53, 0.15)" color="#B7FF35" px={2} py={0.5} borderRadius="full" fontSize="10px">
                    Multimodal Chat
                  </Badge>
                </Flex>
                <Text color="#A5B1A7" fontSize="xs">
                  Prompt, speak in any language, upload references & selectively recreate images
                </Text>
              </Box>
            </Flex>

            {/* Presets and Model Selectors */}
            <Flex wrap="wrap" align="center" gap={2.5}>
              <Select
                size="sm"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                bg="#0F1A11"
                color="#F4F7F0"
                border="1px solid #2A3A2C"
                borderRadius="8px"
                w={{ base: 'full', sm: '190px' }}
                _hover={{ borderColor: '#B7FF35' }}
              >
                {MODEL_OPTIONS.map((m) => (
                  <option key={m} value={m} style={{ background: '#111713' }}>
                    {m}
                  </option>
                ))}
              </Select>

              <Select
                size="sm"
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                bg="#0F1A11"
                color="#F4F7F0"
                border="1px solid #2A3A2C"
                borderRadius="8px"
                w={{ base: 'full', sm: '140px' }}
                _hover={{ borderColor: '#B7FF35' }}
              >
                {STYLE_OPTIONS.map((s) => (
                  <option key={s} value={s} style={{ background: '#111713' }}>
                    {s}
                  </option>
                ))}
              </Select>

              <Select
                size="sm"
                value={aspect}
                onChange={(e) => setAspect(e.target.value)}
                bg="#0F1A11"
                color="#F4F7F0"
                border="1px solid #2A3A2C"
                borderRadius="8px"
                w="130px"
                _hover={{ borderColor: '#B7FF35' }}
              >
                {ASPECT_OPTIONS.map((a) => (
                  <option key={a} value={a} style={{ background: '#111713' }}>
                    {a}
                  </option>
                ))}
              </Select>

              <Select
                size="sm"
                value={quality}
                onChange={(e) => setQuality(e.target.value)}
                bg="#0F1A11"
                color="#F4F7F0"
                border="1px solid #2A3A2C"
                borderRadius="8px"
                w="130px"
                _hover={{ borderColor: '#B7FF35' }}
              >
                {QUALITY_OPTIONS.map((q) => (
                  <option key={q} value={q} style={{ background: '#111713' }}>
                    {q}
                  </option>
                ))}
              </Select>

              <Tooltip label="Clear generation thread">
                <IconButton
                  aria-label="Clear chat"
                  icon={<FiTrash2 />}
                  size="sm"
                  variant="ghost"
                  color="#A5B1A7"
                  _hover={{ color: '#FF4444', bg: '#182019' }}
                  onClick={() => setGenerations([])}
                />
              </Tooltip>
            </Flex>
          </Flex>
        </Box>

        {/* Main Conversation Stream */}
        <Box flex={1} overflowY="auto" pb="140px">
          {generations.length === 0 ? (
            <Flex
              direction="column"
              align="center"
              justify="center"
              p={12}
              textAlign="center"
              border="2px dashed #2A3A2C"
              borderRadius="16px"
              my={8}
            >
              <Text fontSize="48px" mb={3}>✨</Text>
              <Heading size="md" color="#F4F7F0" mb={2}>
                Your Multimodal Creative Canvas is Ready
              </Heading>
              <Text color="#A5B1A7" maxW="480px" fontSize="sm" mb={6}>
                Type an idea below, use the microphone to dictate in your native language, or upload an image to start generating and remixing!
              </Text>
              <Button
                size="sm"
                bg="#B7FF35"
                color="#080B0A"
                fontWeight="bold"
                onClick={() => {
                  setPrompt('A mystical treehouse inside a glowing giant redwood tree with lanterns and fairy bridges');
                }}
              >
                Try Sample Prompt
              </Button>
            </Flex>
          ) : (
            <VStack spacing={6} align="stretch">
              {generations.map((gen) => (
                <Box
                  key={gen.id}
                  bg="#111713"
                  border="1px solid"
                  borderColor={gen.isRecreation ? '#B7FF35' : '#2A3A2C'}
                  borderRadius="16px"
                  p={5}
                  boxShadow="0 8px 32px rgba(0,0,0,0.4)"
                  transition="all 0.2s"
                >
                  {/* User Request Bubble */}
                  <Flex justify="space-between" align="flex-start" mb={4} pb={3} borderBottom="1px solid #1A2A1C">
                    <Flex gap={3} align="flex-start" flex={1}>
                      <Box
                        w="30px"
                        h="30px"
                        borderRadius="full"
                        bg="#182019"
                        border="1px solid #B7FF35"
                        display="flex"
                        alignItems="center"
                        justifyContent="center"
                        fontSize="12px"
                        fontWeight="bold"
                        color="#B7FF35"
                        flexShrink={0}
                      >
                        D
                      </Box>
                      <Box flex={1}>
                        <Flex align="center" gap={2} mb={1}>
                          <Text fontSize="xs" color="#A5B1A7" fontWeight="600">
                            You
                          </Text>
                          <Text fontSize="10px" color="#6B7B6D">
                            {gen.timestamp}
                          </Text>
                          {gen.isRecreation && (
                            <Badge bg="rgba(183,255,53,0.2)" color="#B7FF35" fontSize="10px">
                              Selective Recreation
                            </Badge>
                          )}
                        </Flex>

                        {/* Spoken Language Tag if applicable */}
                        {gen.voiceLanguage && (
                          <Flex align="center" gap={1.5} mb={2}>
                            <Badge bg="#182019" color="#8DDB39" fontSize="10px" px={2} py={0.5} borderRadius="4px">
                              🗣️ Spoken in {gen.voiceLanguage}: "{gen.originalVoiceText}"
                            </Badge>
                          </Flex>
                        )}

                        <Text fontSize="sm" color="#F4F7F0" fontWeight="500">
                          {gen.prompt}
                        </Text>

                        {gen.recreationNote && (
                          <Text fontSize="xs" color="#B7FF35" mt={1}>
                            ✨ {gen.recreationNote}
                          </Text>
                        )}
                      </Box>
                    </Flex>

                    {/* Attached Reference Image Thumbnail */}
                    {gen.referenceImage && (
                      <Box textAlign="right" ml={3}>
                        <Image
                          src={gen.referenceImage}
                          alt="Reference"
                          w="50px"
                          h="50px"
                          objectFit="cover"
                          borderRadius="8px"
                          border="1px solid #B7FF35"
                        />
                        <Text fontSize="9px" color="#A5B1A7" mt={0.5}>
                          Ref Image
                        </Text>
                      </Box>
                    )}
                  </Flex>

                  {/* AI Generation Result Card */}
                  <Box>
                    <Box
                      position="relative"
                      borderRadius="12px"
                      overflow="hidden"
                      border="1px solid #2A3A2C"
                      bg="#080B0A"
                      maxH="520px"
                    >
                      <Image
                        src={gen.imageUrl}
                        alt={gen.prompt}
                        w="100%"
                        maxH="500px"
                        objectFit="contain"
                        transition="transform 0.3s ease"
                      />

                      {/* Top Overlay Badges */}
                      <Flex position="absolute" top={3} left={3} gap={2}>
                        <Badge bg="rgba(8,11,10,0.85)" color="#F4F7F0" backdropFilter="blur(8px)" fontSize="10px" px={2} py={1} borderRadius="6px">
                          {gen.style}
                        </Badge>
                        <Badge bg="rgba(183,255,53,0.2)" color="#B7FF35" backdropFilter="blur(8px)" fontSize="10px" px={2} py={1} borderRadius="6px">
                          {gen.model}
                        </Badge>
                      </Flex>
                    </Box>

                    {/* Interactive Action Toolbar on Each Image */}
                    <Flex
                      justify="space-between"
                      align="center"
                      mt={3}
                      pt={2}
                      borderTop="1px solid #1A2A1C"
                      wrap="wrap"
                      gap={2}
                    >
                      <Flex align="center" gap={2}>
                        {/* Selective Recreate Button */}
                        <Button
                          size="xs"
                          bg="rgba(183, 255, 53, 0.15)"
                          color="#B7FF35"
                          border="1px solid rgba(183, 255, 53, 0.3)"
                          _hover={{ bg: '#B7FF35', color: '#080B0A' }}
                          leftIcon={<FiRefreshCw />}
                          onClick={() => handleOpenSelectiveRecreate(gen)}
                        >
                          Selective Recreate
                        </Button>

                        {/* Ask About Image */}
                        <Button
                          size="xs"
                          variant="ghost"
                          color="#A5B1A7"
                          _hover={{ color: '#F4F7F0', bg: '#182019' }}
                          leftIcon={<FiMessageSquare />}
                          onClick={() => handleAskAboutImage(gen.id)}
                        >
                          Ask Vision AI
                        </Button>

                        {/* Prompt Enhancer Reuse */}
                        <Button
                          size="xs"
                          variant="ghost"
                          color="#A5B1A7"
                          _hover={{ color: '#F4F7F0', bg: '#182019' }}
                          leftIcon={<FiSliders />}
                          onClick={() => setPrompt(gen.prompt)}
                        >
                          Remix Prompt
                        </Button>
                      </Flex>

                      <Flex align="center" gap={2}>
                        <Button
                          as="a"
                          href={gen.imageUrl}
                          download="imagineai-creation.png"
                          target="_blank"
                          size="xs"
                          variant="ghost"
                          color="#A5B1A7"
                          _hover={{ color: '#B7FF35', bg: '#182019' }}
                          leftIcon={<FiDownload />}
                        >
                          Save
                        </Button>
                      </Flex>
                    </Flex>

                    {/* Inline Vision AI inspection response */}
                    {activeQuestionId === gen.id && (
                      <Box mt={3} p={3} bg="#0D120E" border="1px solid #2A3A2C" borderRadius="10px">
                        <Flex justify="space-between" align="center" mb={1}>
                          <Text fontSize="11px" color="#B7FF35" fontWeight="bold">
                            👁️ Imagine Vision Assistant
                          </Text>
                          <Text
                            fontSize="12px"
                            color="#6B7B6D"
                            cursor="pointer"
                            onClick={() => setActiveQuestionId(null)}
                          >
                            ✕
                          </Text>
                        </Flex>
                        <Text fontSize="xs" color="#A5B1A7">
                          {imageAnswer}
                        </Text>
                      </Box>
                    )}
                  </Box>
                </Box>
              ))}
            </VStack>
          )}

          {isGenerating && (
            <Flex
              p={5}
              bg="#111713"
              border="1px dashed #B7FF35"
              borderRadius="16px"
              align="center"
              justify="center"
              gap={3}
              my={4}
            >
              <Text fontSize="20px" animation="spin 1.5s linear infinite">
                ✦
              </Text>
              <Text fontSize="sm" color="#B7FF35" fontWeight="600">
                Generating with {model}... synthesizing visual features
              </Text>
            </Flex>
          )}
        </Box>

        {/* Bottom Floating Multimodal Composer */}
        <Box
          position="fixed"
          bottom="20px"
          left={{ base: '20px', md: '240px' }}
          right="96px"
          zIndex={90}
          bg="#0D120E"
          border="1px solid #3A4A3C"
          borderRadius="18px"
          p={3}
          boxShadow="0 12px 48px rgba(0,0,0,0.8), 0 0 30px rgba(183,255,53,0.15)"
        >
          {/* Attached items pill indicators */}
          {(attachedImage || prompt) && (
            <Flex gap={2} mb={2} px={1} align="center">
              {attachedImage && (
                <Flex align="center" gap={1.5} bg="#182019" px={2.5} py={1} borderRadius="8px" border="1px solid #2A3A2C">
                  <Image src={attachedImage} w="20px" h="20px" borderRadius="4px" objectFit="cover" />
                  <Text fontSize="xs" color="#A5B1A7">Image Reference</Text>
                  <IconButton
                    aria-label="Remove image"
                    icon={<FiX size={12} />}
                    size="xs"
                    variant="ghost"
                    color="#FF4444"
                    onClick={() => setAttachedImage(null)}
                  />
                </Flex>
              )}
            </Flex>
          )}

          <Flex align="flex-end" gap={2}>
            {/* Attachment input */}
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              accept="image/*"
              onChange={handleImageUpload}
            />
            <Tooltip label="Upload image reference (Image-to-Image)">
              <IconButton
                aria-label="Upload reference"
                icon={<FiPaperclip size={18} />}
                variant="ghost"
                color={attachedImage ? '#B7FF35' : '#A5B1A7'}
                bg={attachedImage ? '#182019' : 'transparent'}
                _hover={{ color: '#F4F7F0', bg: '#182019' }}
                borderRadius="10px"
                onClick={() => fileInputRef.current?.click()}
              />
            </Tooltip>

            {/* Voice Assistant & Translation Button */}
            <Tooltip label="Speak in any language (Voice Assistant & Translator)">
              <IconButton
                aria-label="Voice input"
                icon={<FiMic size={18} />}
                variant="ghost"
                color="#A5B1A7"
                _hover={{ color: '#B7FF35', bg: '#182019' }}
                borderRadius="10px"
                onClick={() => setIsVoiceOpen(true)}
              />
            </Tooltip>

            {/* Enhance prompt button */}
            <Tooltip label="✨ Enhance prompt with AI detail">
              <Button
                size="sm"
                variant="outline"
                borderColor="#2A3A2C"
                color="#B7FF35"
                _hover={{ bg: '#1A2A1C', borderColor: '#B7FF35' }}
                borderRadius="10px"
                px={3}
                onClick={handleEnhancePrompt}
                leftIcon={<FiZap size={14} />}
                fontSize="xs"
              >
                Enhance
              </Button>
            </Tooltip>

            {/* Main Textarea */}
            <Textarea
              placeholder="Describe what you want to create, or speak using the mic... (Press Enter to generate)"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleGenerate();
                }
              }}
              minH="44px"
              maxH="120px"
              py={2.5}
              px={3}
              variant="unstyled"
              color="#F4F7F0"
              fontSize="sm"
              _placeholder={{ color: '#6B7B6D' }}
              resize="none"
              flex={1}
            />

            {/* Generate Button */}
            <Button
              bg="#B7FF35"
              color="#080B0A"
              fontWeight="700"
              fontSize="sm"
              borderRadius="12px"
              px={5}
              h="42px"
              _hover={{ bg: '#8DDB39', transform: 'translateY(-1px)' }}
              _active={{ bg: '#6FBB20' }}
              onClick={handleGenerate}
              isLoading={isGenerating}
              rightIcon={<FiSend size={14} />}
            >
              Generate
            </Button>
          </Flex>
        </Box>

        {/* VOICE ASSISTANT & TRANSLATION MODAL */}
        <Modal isOpen={isVoiceOpen} onClose={() => setIsVoiceOpen(false)} isCentered size="lg">
          <ModalOverlay bg="rgba(0,0,0,0.85)" backdropFilter="blur(6px)" />
          <ModalContent bg="#111713" border="1px solid #2A3A2C" borderRadius="18px" color="#F4F7F0">
            <ModalHeader borderBottom="1px solid #1A2A1C" py={4}>
              <Flex align="center" gap={2}>
                <Box w="28px" h="28px" borderRadius="full" bg="#B7FF35" display="flex" alignItems="center" justifyContent="center" color="#080B0A" fontSize="14px">
                  🎤
                </Box>
                <Text fontSize="md" fontWeight="bold">
                  Voice Assistant & Prompt Translator
                </Text>
              </Flex>
            </ModalHeader>
            <ModalCloseButton color="#A5B1A7" />

            <ModalBody py={6}>
              <Text fontSize="xs" color="#A5B1A7" mb={4}>
                Speak your idea naturally in your preferred language. Imagine AI automatically transcribes and translates it into an optimized English image generation prompt!
              </Text>

              {/* Language Selector */}
              <Box mb={5}>
                <Text fontSize="xs" color="#6B7B6D" mb={1.5} textTransform="uppercase" letterSpacing="0.05em">
                  Select Speaking Language
                </Text>
                <Select
                  value={voiceLang.code}
                  onChange={(e) => {
                    const l = LANGUAGES.find((item) => item.code === e.target.value) || LANGUAGES[0];
                    setVoiceLang(l);
                    setSpokenText(l.sample);
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

              {/* Microphone Center Button */}
              <Flex direction="column" align="center" justify="center" py={4}>
                <Box
                  w="76px"
                  h="76px"
                  borderRadius="full"
                  bg={isRecording ? '#FF4444' : '#182019'}
                  border="2px solid"
                  borderColor={isRecording ? '#FF4444' : '#B7FF35'}
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                  cursor="pointer"
                  onClick={handleToggleRecord}
                  boxShadow={isRecording ? '0 0 25px rgba(255,68,68,0.5)' : '0 0 20px rgba(183,255,53,0.3)'}
                  transition="all 0.25s"
                  _hover={{ transform: 'scale(1.05)' }}
                >
                  <FiMic size={32} color={isRecording ? '#F4F7F0' : '#B7FF35'} />
                </Box>
                <Text fontSize="xs" color={isRecording ? '#FF4444' : '#B7FF35'} fontWeight="600" mt={3}>
                  {isRecording ? 'Listening... Speak now' : 'Tap microphone to speak'}
                </Text>
              </Flex>

              {/* Transcription & Translation Card */}
              <Box bg="#0D120E" p={4} borderRadius="12px" border="1px solid #2A3A2C" mt={3}>
                <Text fontSize="10px" color="#6B7B6D" textTransform="uppercase" fontWeight="bold" mb={1}>
                  Transcribed ({voiceLang.name})
                </Text>
                <Text fontSize="sm" color="#F4F7F0" mb={3}>
                  "{spokenText}"
                </Text>

                <Box h="1px" bg="#1A2A1C" my={2} />

                <Text fontSize="10px" color="#8DDB39" textTransform="uppercase" fontWeight="bold" mb={1}>
                  ✨ Translated & Enhanced Generation Prompt
                </Text>
                <Text fontSize="sm" color="#B7FF35" fontWeight="500">
                  {translatedPrompt}
                </Text>
              </Box>
            </ModalBody>

            <ModalFooter borderTop="1px solid #1A2A1C" py={3}>
              <Button size="sm" variant="ghost" color="#A5B1A7" mr={3} onClick={() => setIsVoiceOpen(false)}>
                Cancel
              </Button>
              <Button size="sm" bg="#B7FF35" color="#080B0A" fontWeight="bold" onClick={handleApplyVoicePrompt}>
                Use This Prompt
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>

        {/* SELECTIVE RECREATION MODAL WITH INTERACTIVE CANVAS CIRCLING & MASKING */}
        <Modal isOpen={isRecreationOpen} onClose={() => setIsRecreationOpen(false)} isCentered size="2xl">
          <ModalOverlay bg="rgba(0,0,0,0.88)" backdropFilter="blur(8px)" />
          <ModalContent bg="#111713" border="1px solid #2A3A2C" borderRadius="20px" color="#F4F7F0" maxW="720px">
            <ModalHeader borderBottom="1px solid #1A2A1C" py={4}>
              <Flex align="center" justify="space-between">
                <Flex align="center" gap={2.5}>
                  <Box w="30px" h="30px" borderRadius="full" bg="#B7FF35" display="flex" alignItems="center" justifyContent="center" color="#080B0A" fontSize="15px">
                    ⭕
                  </Box>
                  <Box>
                    <Text fontSize="md" fontWeight="bold">
                      Selective Recreate — Circle & Inpaint Region
                    </Text>
                    <Text fontSize="xs" color="#A5B1A7" fontWeight="normal">
                      Click and drag directly on the image to circle the exact area you want recreated
                    </Text>
                  </Box>
                </Flex>
                <ModalCloseButton position="static" color="#A5B1A7" />
              </Flex>
            </ModalHeader>

            <ModalBody py={4}>
              {/* Interactive Mask Canvas */}
              {selectedTargetImage && (
                <Box mb={4}>
                  <InteractiveCanvasMask
                    imageUrl={selectedTargetImage.imageUrl}
                    onMaskChange={(hasMask, dataUrl) => {
                      setHasMaskSelected(hasMask);
                      setMaskDataUrl(dataUrl || null);
                    }}
                  />
                </Box>
              )}

              {/* Inpainting Instruction Input */}
              <Box mb={3}>
                <Text fontSize="xs" color="#A5B1A7" fontWeight="600" mb={1.5} textTransform="uppercase" letterSpacing="0.05em">
                  What should appear in the circled region?
                </Text>
                <Input
                  value={recreationInstruction}
                  onChange={(e) => setRecreationInstruction(e.target.value)}
                  placeholder="e.g. Add a glowing golden visor with neon cyber reflections, or make flowers bloom"
                  bg="#0F1A11"
                  color="#F4F7F0"
                  border="1px solid #2A3A2C"
                  borderRadius="10px"
                  size="sm"
                  _focus={{ borderColor: '#B7FF35' }}
                />
              </Box>

              <Flex justify="space-between" align="center" bg="#0D120E" p={2.5} borderRadius="8px" border="1px solid #1A2A1C">
                <Text fontSize="11px" color="#6B7B6D">
                  Region targeted: <span style={{ color: hasMaskSelected ? '#B7FF35' : '#FFB800', fontWeight: 'bold' }}>{hasMaskSelected ? '✓ Active Canvas Circle / Mask' : '⚠️ No area circled yet (Full image will be varied)'}</span>
                </Text>
                <Badge bg="rgba(183, 255, 53, 0.15)" color="#B7FF35" fontSize="10px">
                  Inpaint Engine Ready
                </Badge>
              </Flex>
            </ModalBody>

            <ModalFooter borderTop="1px solid #1A2A1C" py={3}>
              <Button size="sm" variant="ghost" color="#A5B1A7" mr={3} onClick={() => setIsRecreationOpen(false)}>
                Cancel
              </Button>
              <Button
                size="sm"
                bg="#B7FF35"
                color="#080B0A"
                fontWeight="bold"
                onClick={handleApplySelectiveRecreation}
                leftIcon={<Text>✨</Text>}
                _hover={{ bg: '#8DDB39' }}
              >
                Recreate Circled Region
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </Box>
    </WorkspaceLayout>
  );
};

export default CreateStudio;
