import React, { useState } from 'react';
import {
  Box, Flex, Text, Heading, Button, Textarea, Select, Icon,
} from '@chakra-ui/react';
import { keyframes } from '@emotion/react';
import WorkspaceLayout from '../components/WorkspaceLayout';

const pulse = keyframes`
  0% { box-shadow: 0 0 0 0 rgba(183,255,53,0.5); }
  70% { box-shadow: 0 0 0 20px rgba(183,255,53,0); }
  100% { box-shadow: 0 0 0 0 rgba(183,255,53,0); }
`;

const MicIcon: React.FC<{ size?: number }> = ({ size = 48 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="#B7FF35" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
    <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
    <line x1="12" y1="19" x2="12" y2="23" />
    <line x1="8" y1="23" x2="16" y2="23" />
  </svg>
);

const PlayIcon: React.FC = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="#080B0A" stroke="none">
    <polygon points="5,3 19,12 5,21" />
  </svg>
);

const SwapIcon: React.FC = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#B7FF35" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="16 3 21 3 21 8" /><line x1="4" y1="20" x2="21" y2="3" />
    <polyline points="21 16 21 21 16 21" /><line x1="15" y1="15" x2="21" y2="21" />
  </svg>
);

type TabKey = 'voice' | 'translate' | 'speech';

const LANGUAGES = ['English', 'Spanish', 'French', 'German', 'Hindi', 'Japanese'];

const VoiceTranslation: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabKey>('voice');
  const [isListening, setIsListening] = useState(false);
  const [sourceText, setSourceText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [sourceLang, setSourceLang] = useState('English');
  const [targetLang, setTargetLang] = useState('Spanish');
  const [speechText, setSpeechText] = useState('');
  const [speechLang, setSpeechLang] = useState('English');

  const tabs: { key: TabKey; label: string }[] = [
    { key: 'voice', label: 'Voice Assistant' },
    { key: 'translate', label: 'Translate' },
    { key: 'speech', label: 'Speech' },
  ];

  const handleTranslate = () => {
    const mockTranslations: Record<string, string> = {
      'Hello': 'Hola',
      'Good morning': 'Buenos días',
      'How are you?': '¿Cómo estás?',
      'Thank you': 'Gracias',
    };
    setTranslatedText(
      mockTranslations[sourceText] ||
        `[${targetLang}] ${sourceText.split('').reverse().join('')}`
    );
  };

  return (
    <WorkspaceLayout>
      <Box p={8} minH="100vh" bg="#080B0A">
        {/* Header */}
        <Flex align="center" justify="space-between" mb={8}>
          <Box>
            <Heading size="lg" color="#F4F7F0" fontWeight={700}>
              Voice & Translation
            </Heading>
            <Text color="#A5B1A7" mt={1} fontSize="sm">
              Speak, translate, and convert text to speech
            </Text>
          </Box>
        </Flex>

        {/* Tab Buttons */}
        <Flex gap={2} mb={8}>
          {tabs.map((tab) => (
            <Button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              bg={activeTab === tab.key ? '#B7FF35' : '#111713'}
              color={activeTab === tab.key ? '#080B0A' : '#A5B1A7'}
              border="1px solid"
              borderColor={activeTab === tab.key ? '#B7FF35' : '#2A3A2C'}
              borderRadius="10px"
              px={6}
              py={2}
              fontWeight={600}
              fontSize="sm"
              _hover={{
                bg: activeTab === tab.key ? '#8DDB39' : '#1A2A1C',
                color: activeTab === tab.key ? '#080B0A' : '#F4F7F0',
              }}
              transition="all 0.2s ease"
            >
              {tab.label}
            </Button>
          ))}
        </Flex>

        {/* Voice Assistant Tab */}
        {activeTab === 'voice' && (
          <Flex direction="column" align="center" justify="center" minH="60vh">
            <Box
              bg="#111713"
              borderRadius="24px"
              border="1px solid #2A3A2C"
              p={12}
              textAlign="center"
              maxW="480px"
              w="100%"
            >
              {/* Status */}
              <Flex align="center" justify="center" gap={2} mb={8}>
                <Box
                  w="8px"
                  h="8px"
                  borderRadius="full"
                  bg={isListening ? '#B7FF35' : '#A5B1A7'}
                  boxShadow={isListening ? '0 0 12px #B7FF35' : 'none'}
                />
                <Text
                  color={isListening ? '#B7FF35' : '#A5B1A7'}
                  fontSize="sm"
                  fontWeight={500}
                  letterSpacing="0.05em"
                  textTransform="uppercase"
                >
                  {isListening ? 'Listening...' : 'Ready'}
                </Text>
              </Flex>

              {/* Microphone Button */}
              <Flex justify="center" mb={6}>
                <Box
                  as="button"
                  onClick={() => setIsListening(!isListening)}
                  w="140px"
                  h="140px"
                  borderRadius="full"
                  border="3px solid"
                  borderColor={isListening ? '#B7FF35' : '#2A3A2C'}
                  bg={isListening ? 'rgba(183,255,53,0.08)' : '#182019'}
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                  cursor="pointer"
                  transition="all 0.3s ease"
                  animation={isListening ? `${pulse} 1.5s infinite` : 'none'}
                  _hover={{
                    borderColor: '#B7FF35',
                    bg: 'rgba(183,255,53,0.12)',
                    animation: `${pulse} 1.5s infinite`,
                    transform: 'scale(1.05)',
                  }}
                >
                  <MicIcon size={48} />
                </Box>
              </Flex>

              <Text color="#F4F7F0" fontSize="lg" fontWeight={600} mb={1}>
                Tap to speak
              </Text>
              <Text color="#A5B1A7" fontSize="sm">
                Press the microphone button and start talking
              </Text>

              {/* Audio visualization bars */}
              {isListening && (
                <Flex justify="center" gap="3px" mt={6} h="40px" align="flex-end">
                  {[20, 35, 28, 40, 18, 32, 25, 38, 22, 30, 15, 35].map(
                    (h, i) => (
                      <Box
                        key={i}
                        w="4px"
                        borderRadius="2px"
                        bg="#B7FF35"
                        h={`${h}px`}
                        opacity={0.6 + Math.random() * 0.4}
                        animation={`${keyframes`
                          0%, 100% { height: ${h * 0.4}px; }
                          50% { height: ${h}px; }
                        `} ${0.4 + i * 0.08}s ease-in-out infinite`}
                      />
                    )
                  )}
                </Flex>
              )}
            </Box>

            {/* Recent Transcriptions */}
            <Box mt={8} maxW="480px" w="100%">
              <Text color="#A5B1A7" fontSize="xs" mb={3} textTransform="uppercase" letterSpacing="0.1em">
                Recent Transcriptions
              </Text>
              {['Create an image of a sunset over mountains', 'Generate a portrait in watercolor style', 'Make a logo with modern geometric shapes'].map(
                (t, i) => (
                  <Box
                    key={i}
                    bg="#111713"
                    border="1px solid #2A3A2C"
                    borderRadius="10px"
                    p={3}
                    mb={2}
                    _hover={{ bg: '#1A2A1C', borderColor: '#B7FF35' }}
                    transition="all 0.2s"
                    cursor="pointer"
                  >
                    <Text color="#F4F7F0" fontSize="sm">"{t}"</Text>
                    <Text color="#A5B1A7" fontSize="xs" mt={1}>{i === 0 ? '2 min ago' : i === 1 ? '15 min ago' : '1 hour ago'}</Text>
                  </Box>
                )
              )}
            </Box>
          </Flex>
        )}

        {/* Translate Tab */}
        {activeTab === 'translate' && (
          <Box maxW="900px" mx="auto">
            <Box
              bg="#111713"
              borderRadius="16px"
              border="1px solid #2A3A2C"
              overflow="hidden"
            >
              {/* Language Selectors */}
              <Flex
                bg="#0D120E"
                p={4}
                align="center"
                justify="space-between"
                borderBottom="1px solid #2A3A2C"
              >
                <Select
                  value={sourceLang}
                  onChange={(e) => setSourceLang(e.target.value)}
                  bg="#0F1A11"
                  color="#F4F7F0"
                  border="1px solid #2A3A2C"
                  borderRadius="8px"
                  w="200px"
                  _hover={{ borderColor: '#B7FF35' }}
                  _focus={{ borderColor: '#B7FF35', boxShadow: '0 0 0 1px #B7FF35' }}
                  sx={{ option: { bg: '#111713', color: '#F4F7F0' } }}
                >
                  {LANGUAGES.map((l) => (
                    <option key={l} value={l}>{l}</option>
                  ))}
                </Select>

                <Box
                  as="button"
                  onClick={() => {
                    const tmp = sourceLang;
                    setSourceLang(targetLang);
                    setTargetLang(tmp);
                  }}
                  p={2}
                  borderRadius="8px"
                  _hover={{ bg: '#1A2A1C' }}
                  transition="all 0.2s"
                  cursor="pointer"
                >
                  <SwapIcon />
                </Box>

                <Select
                  value={targetLang}
                  onChange={(e) => setTargetLang(e.target.value)}
                  bg="#0F1A11"
                  color="#F4F7F0"
                  border="1px solid #2A3A2C"
                  borderRadius="8px"
                  w="200px"
                  _hover={{ borderColor: '#B7FF35' }}
                  _focus={{ borderColor: '#B7FF35', boxShadow: '0 0 0 1px #B7FF35' }}
                  sx={{ option: { bg: '#111713', color: '#F4F7F0' } }}
                >
                  {LANGUAGES.map((l) => (
                    <option key={l} value={l}>{l}</option>
                  ))}
                </Select>
              </Flex>

              {/* Text Areas */}
              <Flex>
                <Box flex={1} p={5} borderRight="1px solid #2A3A2C">
                  <Text color="#A5B1A7" fontSize="xs" mb={2} textTransform="uppercase" letterSpacing="0.08em">
                    Source ({sourceLang})
                  </Text>
                  <Textarea
                    value={sourceText}
                    onChange={(e) => setSourceText(e.target.value)}
                    placeholder="Enter text to translate..."
                    bg="transparent"
                    color="#F4F7F0"
                    border="none"
                    _focus={{ boxShadow: 'none' }}
                    _placeholder={{ color: '#A5B1A7' }}
                    minH="200px"
                    resize="none"
                    fontSize="md"
                  />
                  <Flex justify="space-between" align="center" mt={3}>
                    <Text color="#A5B1A7" fontSize="xs">
                      {sourceText.length} characters
                    </Text>
                  </Flex>
                </Box>

                <Box flex={1} p={5} bg="rgba(183,255,53,0.02)">
                  <Text color="#A5B1A7" fontSize="xs" mb={2} textTransform="uppercase" letterSpacing="0.08em">
                    Translation ({targetLang})
                  </Text>
                  <Box minH="200px">
                    <Text color="#F4F7F0" fontSize="md" whiteSpace="pre-wrap">
                      {translatedText || (
                        <Text as="span" color="#A5B1A7" fontStyle="italic">
                          Translation will appear here...
                        </Text>
                      )}
                    </Text>
                  </Box>
                </Box>
              </Flex>

              {/* Translate Button */}
              <Flex p={4} borderTop="1px solid #2A3A2C" justify="flex-end" gap={3}>
                <Button
                  onClick={() => { setSourceText(''); setTranslatedText(''); }}
                  bg="transparent"
                  color="#A5B1A7"
                  border="1px solid #2A3A2C"
                  borderRadius="10px"
                  _hover={{ bg: '#1A2A1C', color: '#F4F7F0' }}
                  size="md"
                >
                  Clear
                </Button>
                <Button
                  onClick={handleTranslate}
                  bg="#B7FF35"
                  color="#080B0A"
                  borderRadius="10px"
                  px={8}
                  fontWeight={700}
                  _hover={{ bg: '#8DDB39' }}
                  _active={{ bg: '#7BC82E' }}
                  size="md"
                  isDisabled={!sourceText.trim()}
                >
                  Translate
                </Button>
              </Flex>
            </Box>

            {/* Translation History */}
            <Box mt={8}>
              <Text color="#A5B1A7" fontSize="xs" mb={3} textTransform="uppercase" letterSpacing="0.1em">
                Translation History
              </Text>
              {[
                { from: 'Hello, how are you?', to: 'Hola, ¿cómo estás?', src: 'English', tgt: 'Spanish' },
                { from: 'Good morning', to: 'Bonjour', src: 'English', tgt: 'French' },
                { from: 'Thank you very much', to: 'Vielen Dank', src: 'English', tgt: 'German' },
              ].map((item, i) => (
                <Box
                  key={i}
                  bg="#111713"
                  border="1px solid #2A3A2C"
                  borderRadius="10px"
                  p={4}
                  mb={2}
                  _hover={{ borderColor: '#B7FF35' }}
                  transition="all 0.2s"
                >
                  <Flex justify="space-between" align="center">
                    <Box>
                      <Text color="#F4F7F0" fontSize="sm">"{item.from}"</Text>
                      <Text color="#B7FF35" fontSize="sm" mt={1}>→ "{item.to}"</Text>
                    </Box>
                    <Text color="#A5B1A7" fontSize="xs">{item.src} → {item.tgt}</Text>
                  </Flex>
                </Box>
              ))}
            </Box>
          </Box>
        )}

        {/* Speech Tab */}
        {activeTab === 'speech' && (
          <Box maxW="640px" mx="auto">
            <Box
              bg="#111713"
              borderRadius="16px"
              border="1px solid #2A3A2C"
              p={6}
            >
              <Heading size="sm" color="#F4F7F0" mb={1}>
                Text to Speech
              </Heading>
              <Text color="#A5B1A7" fontSize="sm" mb={6}>
                Convert your text into natural-sounding speech
              </Text>

              <Text color="#A5B1A7" fontSize="xs" mb={2} textTransform="uppercase" letterSpacing="0.08em">
                Language & Voice
              </Text>
              <Select
                value={speechLang}
                onChange={(e) => setSpeechLang(e.target.value)}
                bg="#0F1A11"
                color="#F4F7F0"
                border="1px solid #2A3A2C"
                borderRadius="8px"
                mb={5}
                _hover={{ borderColor: '#B7FF35' }}
                _focus={{ borderColor: '#B7FF35', boxShadow: '0 0 0 1px #B7FF35' }}
                sx={{ option: { bg: '#111713', color: '#F4F7F0' } }}
              >
                {LANGUAGES.map((l) => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </Select>

              <Text color="#A5B1A7" fontSize="xs" mb={2} textTransform="uppercase" letterSpacing="0.08em">
                Enter Text
              </Text>
              <Textarea
                value={speechText}
                onChange={(e) => setSpeechText(e.target.value)}
                placeholder="Type or paste text you want to hear spoken aloud..."
                bg="#0F1A11"
                color="#F4F7F0"
                border="1px solid #2A3A2C"
                borderRadius="10px"
                _hover={{ borderColor: '#B7FF35' }}
                _focus={{ borderColor: '#B7FF35', boxShadow: '0 0 0 1px #B7FF35' }}
                _placeholder={{ color: '#A5B1A7' }}
                minH="160px"
                resize="none"
                mb={4}
              />

              <Text color="#A5B1A7" fontSize="xs" mb={4}>
                {speechText.length} / 5000 characters
              </Text>

              {/* Speed & Pitch Controls */}
              <Flex gap={4} mb={6}>
                <Box flex={1}>
                  <Text color="#A5B1A7" fontSize="xs" mb={2} textTransform="uppercase" letterSpacing="0.08em">
                    Speed
                  </Text>
                  <Flex gap={2}>
                    {['0.5x', '0.75x', '1x', '1.25x', '1.5x'].map((s) => (
                      <Box
                        key={s}
                        as="button"
                        px={3}
                        py={1}
                        borderRadius="6px"
                        bg={s === '1x' ? '#B7FF35' : '#0F1A11'}
                        color={s === '1x' ? '#080B0A' : '#A5B1A7'}
                        border="1px solid"
                        borderColor={s === '1x' ? '#B7FF35' : '#2A3A2C'}
                        fontSize="xs"
                        fontWeight={600}
                        cursor="pointer"
                        _hover={{ borderColor: '#B7FF35' }}
                        transition="all 0.2s"
                      >
                        {s}
                      </Box>
                    ))}
                  </Flex>
                </Box>
              </Flex>

              {/* Playback Preview */}
              <Box
                bg="#0D120E"
                borderRadius="12px"
                p={4}
                border="1px solid #2A3A2C"
                mb={5}
              >
                <Flex align="center" gap={4}>
                  <Box
                    as="button"
                    w="44px"
                    h="44px"
                    borderRadius="full"
                    bg="#B7FF35"
                    display="flex"
                    alignItems="center"
                    justifyContent="center"
                    cursor="pointer"
                    _hover={{ bg: '#8DDB39', transform: 'scale(1.08)' }}
                    transition="all 0.2s"
                    flexShrink={0}
                  >
                    <PlayIcon />
                  </Box>
                  {/* Waveform */}
                  <Flex flex={1} gap="2px" align="center" h="32px">
                    {Array.from({ length: 50 }, (_, i) => (
                      <Box
                        key={i}
                        w="3px"
                        h={`${8 + Math.sin(i * 0.5) * 12 + Math.random() * 8}px`}
                        borderRadius="1px"
                        bg={i < 20 ? '#B7FF35' : '#2A3A2C'}
                        opacity={i < 20 ? 0.9 : 0.5}
                      />
                    ))}
                  </Flex>
                  <Text color="#A5B1A7" fontSize="xs" flexShrink={0}>
                    0:00 / 0:00
                  </Text>
                </Flex>
              </Box>

              <Flex gap={3}>
                <Button
                  flex={1}
                  bg="#B7FF35"
                  color="#080B0A"
                  borderRadius="10px"
                  fontWeight={700}
                  _hover={{ bg: '#8DDB39' }}
                  _active={{ bg: '#7BC82E' }}
                  isDisabled={!speechText.trim()}
                  leftIcon={<PlayIcon />}
                >
                  Generate Speech
                </Button>
                <Button
                  bg="transparent"
                  color="#A5B1A7"
                  border="1px solid #2A3A2C"
                  borderRadius="10px"
                  _hover={{ bg: '#1A2A1C', color: '#F4F7F0' }}
                  px={6}
                >
                  Download
                </Button>
              </Flex>
            </Box>
          </Box>
        )}
      </Box>
    </WorkspaceLayout>
  );
};

export default VoiceTranslation;
