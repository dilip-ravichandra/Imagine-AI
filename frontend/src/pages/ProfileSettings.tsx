import React, { useState } from 'react';
import {
  Box, Flex, Text, Heading, Button, Input, Switch, Progress,
} from '@chakra-ui/react';
import WorkspaceLayout from '../components/WorkspaceLayout';

type SettingsSection =
  | 'account'
  | 'preferences'
  | 'appearance'
  | 'languages'
  | 'accessibility'
  | 'privacy'
  | 'apikeys';

interface NavItem {
  key: SettingsSection;
  label: string;
  icon: React.ReactNode;
}

const UserIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
);
const SlidersIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/></svg>
);
const PaletteIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="13.5" cy="6.5" r="0.5" fill="currentColor"/><circle cx="17.5" cy="10.5" r="0.5" fill="currentColor"/><circle cx="8.5" cy="7.5" r="0.5" fill="currentColor"/><circle cx="6.5" cy="12.5" r="0.5" fill="currentColor"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/></svg>
);
const GlobeIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
);
const AccessibilityIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="4" r="1"/><path d="M7 21l3-9"/><path d="M17 21l-3-9"/><path d="M12 12l-4-3h8l-4 3z"/></svg>
);
const ShieldIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
);
const KeyIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>
);

const NAV_ITEMS: NavItem[] = [
  { key: 'account', label: 'Account', icon: <UserIcon /> },
  { key: 'preferences', label: 'Preferences', icon: <SlidersIcon /> },
  { key: 'appearance', label: 'Appearance', icon: <PaletteIcon /> },
  { key: 'languages', label: 'Languages', icon: <GlobeIcon /> },
  { key: 'accessibility', label: 'Accessibility', icon: <AccessibilityIcon /> },
  { key: 'privacy', label: 'Privacy', icon: <ShieldIcon /> },
  { key: 'apikeys', label: 'API Keys', icon: <KeyIcon /> },
];

const SettingToggle: React.FC<{ label: string; desc: string; defaultChecked?: boolean }> = ({
  label,
  desc,
  defaultChecked,
}) => {
  const [checked, setChecked] = useState(defaultChecked ?? false);
  return (
    <Flex
      justify="space-between"
      align="center"
      py={4}
      borderBottom="1px solid #2A3A2C"
    >
      <Box>
        <Text color="#F4F7F0" fontSize="sm" fontWeight={500}>{label}</Text>
        <Text color="#A5B1A7" fontSize="xs" mt={0.5}>{desc}</Text>
      </Box>
      <Switch
        isChecked={checked}
        onChange={() => setChecked(!checked)}
        sx={{
          'span.chakra-switch__track': {
            bg: checked ? '#B7FF35' : '#2A3A2C',
          },
          'span.chakra-switch__track[data-checked]': {
            bg: '#B7FF35',
          },
        }}
      />
    </Flex>
  );
};

const SettingInput: React.FC<{ label: string; value: string; readOnly?: boolean }> = ({
  label,
  value,
  readOnly,
}) => (
  <Box mb={4}>
    <Text color="#A5B1A7" fontSize="xs" mb={1.5} textTransform="uppercase" letterSpacing="0.08em">
      {label}
    </Text>
    <Input
      defaultValue={value}
      readOnly={readOnly}
      bg="#0F1A11"
      color="#F4F7F0"
      border="1px solid #2A3A2C"
      borderRadius="8px"
      _hover={readOnly ? {} : { borderColor: '#B7FF35' }}
      _focus={readOnly ? {} : { borderColor: '#B7FF35', boxShadow: '0 0 0 1px #B7FF35' }}
      _readOnly={{ opacity: 0.7, cursor: 'not-allowed' }}
    />
  </Box>
);

const ProfileSettings: React.FC = () => {
  const [activeSection, setActiveSection] = useState<SettingsSection>('account');

  const renderContent = () => {
    switch (activeSection) {
      case 'account':
        return (
          <Box>
            <Heading size="md" color="#F4F7F0" mb={1}>My Profile</Heading>
            <Text color="#A5B1A7" fontSize="sm" mb={6}>Manage your account information and subscription</Text>

            {/* Avatar & Info */}
            <Box bg="#111713" borderRadius="16px" border="1px solid #2A3A2C" p={6} mb={6}>
              <Flex gap={5} align="center" mb={6}>
                <Box
                  w="80px"
                  h="80px"
                  borderRadius="full"
                  overflow="hidden"
                  border="3px solid #B7FF35"
                  flexShrink={0}
                >
                  <Box
                    as="img"
                    src="https://api.dicebear.com/7.x/avataaars/svg?seed=ImagineUser&backgroundColor=182019"
                    alt="Avatar"
                    w="100%"
                    h="100%"
                  />
                </Box>
                <Box flex={1}>
                  <Flex align="center" gap={3} mb={1}>
                    <Text color="#F4F7F0" fontSize="lg" fontWeight={700}>
                      Alex Johnson
                    </Text>
                    <Box
                      bg="rgba(183,255,53,0.15)"
                      color="#B7FF35"
                      px={3}
                      py={0.5}
                      borderRadius="full"
                      fontSize="xs"
                      fontWeight={700}
                      border="1px solid rgba(183,255,53,0.3)"
                    >
                      PRO
                    </Box>
                  </Flex>
                  <Text color="#A5B1A7" fontSize="sm">alex.johnson@email.com</Text>
                  <Text color="#A5B1A7" fontSize="xs" mt={1}>Member since Jan 2025</Text>
                </Box>
                <Button
                  variant="outline"
                  borderColor="#B7FF35"
                  color="#B7FF35"
                  borderRadius="10px"
                  size="sm"
                  _hover={{ bg: 'rgba(183,255,53,0.1)' }}
                >
                  Edit Profile
                </Button>
              </Flex>

              <Flex gap={5}>
                <Box flex={1}>
                  <SettingInput label="Full Name" value="Alex Johnson" />
                </Box>
                <Box flex={1}>
                  <SettingInput label="Email" value="alex.johnson@email.com" readOnly />
                </Box>
              </Flex>
              <Flex gap={5}>
                <Box flex={1}>
                  <SettingInput label="Username" value="@alexj_imagine" />
                </Box>
                <Box flex={1}>
                  <SettingInput label="Phone" value="+1 (555) 123-4567" />
                </Box>
              </Flex>
            </Box>

            {/* Usage */}
            <Box bg="#111713" borderRadius="16px" border="1px solid #2A3A2C" p={6}>
              <Flex justify="space-between" align="center" mb={4}>
                <Box>
                  <Text color="#F4F7F0" fontWeight={600}>Usage This Month</Text>
                  <Text color="#A5B1A7" fontSize="sm">Pro Plan — resets Dec 1, 2026</Text>
                </Box>
                <Button
                  size="sm"
                  bg="transparent"
                  border="1px solid #2A3A2C"
                  color="#A5B1A7"
                  borderRadius="8px"
                  _hover={{ bg: '#1A2A1C', color: '#F4F7F0' }}
                >
                  Upgrade Plan
                </Button>
              </Flex>

              <Box mb={4}>
                <Flex justify="space-between" mb={2}>
                  <Text color="#A5B1A7" fontSize="sm">Images Generated</Text>
                  <Text color="#F4F7F0" fontSize="sm" fontWeight={600}>1,340 / 5,000</Text>
                </Flex>
                <Box bg="#0D120E" borderRadius="full" h="10px" overflow="hidden">
                  <Box bg="#B7FF35" h="100%" w="26.8%" borderRadius="full" transition="width 0.5s ease" />
                </Box>
              </Box>

              <Grid gap={4}>
                {[
                  { label: 'API Calls', used: '4,210', total: '10,000', pct: 42.1 },
                  { label: 'Storage Used', used: '2.4 GB', total: '10 GB', pct: 24 },
                  { label: 'Training Hours', used: '12', total: '50', pct: 24 },
                ].map((item) => (
                  <Box key={item.label}>
                    <Flex justify="space-between" mb={2}>
                      <Text color="#A5B1A7" fontSize="sm">{item.label}</Text>
                      <Text color="#F4F7F0" fontSize="sm" fontWeight={600}>
                        {item.used} / {item.total}
                      </Text>
                    </Flex>
                    <Box bg="#0D120E" borderRadius="full" h="6px" overflow="hidden">
                      <Box bg="#8DDB39" h="100%" w={`${item.pct}%`} borderRadius="full" transition="width 0.5s ease" />
                    </Box>
                  </Box>
                ))}
              </Grid>
            </Box>
          </Box>
        );

      case 'preferences':
        return (
          <Box>
            <Heading size="md" color="#F4F7F0" mb={1}>Preferences</Heading>
            <Text color="#A5B1A7" fontSize="sm" mb={6}>Customize your generation defaults and workflow</Text>
            <Box bg="#111713" borderRadius="16px" border="1px solid #2A3A2C" p={6}>
              <SettingToggle label="Auto-save generations" desc="Automatically save all generated images to your gallery" defaultChecked />
              <SettingToggle label="HD upscale by default" desc="Apply 2× upscaling to all generated images" />
              <SettingToggle label="NSFW content filter" desc="Enable content filtering on generated outputs" defaultChecked />
              <SettingToggle label="Prompt enhancement" desc="Use AI to automatically enhance your prompts" defaultChecked />
              <SettingToggle label="Batch generation" desc="Generate multiple variations per prompt" />
              <Box mt={4}>
                <SettingInput label="Default negative prompt" value="blurry, low quality, distorted, watermark" />
                <SettingInput label="Default steps" value="30" />
                <SettingInput label="Default CFG scale" value="7.5" />
              </Box>
            </Box>
          </Box>
        );

      case 'appearance':
        return (
          <Box>
            <Heading size="md" color="#F4F7F0" mb={1}>Appearance</Heading>
            <Text color="#A5B1A7" fontSize="sm" mb={6}>Customize the look and feel of your workspace</Text>
            <Box bg="#111713" borderRadius="16px" border="1px solid #2A3A2C" p={6}>
              <Text color="#F4F7F0" fontSize="sm" fontWeight={600} mb={4}>Theme</Text>
              <Flex gap={3} mb={6}>
                {['Dark', 'Light', 'System'].map((t) => (
                  <Box
                    key={t}
                    as="button"
                    px={6}
                    py={3}
                    borderRadius="10px"
                    bg={t === 'Dark' ? 'rgba(183,255,53,0.1)' : '#0F1A11'}
                    border="1px solid"
                    borderColor={t === 'Dark' ? '#B7FF35' : '#2A3A2C'}
                    color={t === 'Dark' ? '#B7FF35' : '#A5B1A7'}
                    fontWeight={600}
                    fontSize="sm"
                    cursor="pointer"
                    _hover={{ borderColor: '#B7FF35' }}
                    transition="all 0.2s"
                  >
                    {t}
                  </Box>
                ))}
              </Flex>
              <SettingToggle label="Compact sidebar" desc="Reduce sidebar width for more workspace" />
              <SettingToggle label="Show grid lines" desc="Display grid overlay in the image editor" defaultChecked />
              <SettingToggle label="Animations" desc="Enable UI motion and transitions" defaultChecked />
            </Box>
          </Box>
        );

      case 'languages':
        return (
          <Box>
            <Heading size="md" color="#F4F7F0" mb={1}>Languages</Heading>
            <Text color="#A5B1A7" fontSize="sm" mb={6}>Set your preferred interface and translation languages</Text>
            <Box bg="#111713" borderRadius="16px" border="1px solid #2A3A2C" p={6}>
              <SettingInput label="Interface language" value="English (US)" />
              <SettingInput label="Translation default source" value="English" />
              <SettingInput label="Translation default target" value="Spanish" />
              <SettingToggle label="Auto-detect language" desc="Automatically detect the input language when translating" defaultChecked />
            </Box>
          </Box>
        );

      case 'accessibility':
        return (
          <Box>
            <Heading size="md" color="#F4F7F0" mb={1}>Accessibility</Heading>
            <Text color="#A5B1A7" fontSize="sm" mb={6}>Adjust accessibility settings for a better experience</Text>
            <Box bg="#111713" borderRadius="16px" border="1px solid #2A3A2C" p={6}>
              <SettingToggle label="High contrast mode" desc="Increase contrast across all interface elements" />
              <SettingToggle label="Reduced motion" desc="Disable animations and transitions" />
              <SettingToggle label="Screen reader optimization" desc="Enhanced labels and ARIA attributes" defaultChecked />
              <SettingToggle label="Keyboard navigation" desc="Full keyboard navigation support" defaultChecked />
              <SettingInput label="Font size multiplier" value="1.0" />
            </Box>
          </Box>
        );

      case 'privacy':
        return (
          <Box>
            <Heading size="md" color="#F4F7F0" mb={1}>Privacy & Security</Heading>
            <Text color="#A5B1A7" fontSize="sm" mb={6}>Manage your data privacy and security settings</Text>
            <Box bg="#111713" borderRadius="16px" border="1px solid #2A3A2C" p={6}>
              <SettingToggle label="Two-factor authentication" desc="Add an extra layer of security to your account" defaultChecked />
              <SettingToggle label="Usage analytics" desc="Help us improve by sharing anonymous usage data" defaultChecked />
              <SettingToggle label="Public profile" desc="Allow others to see your profile and shared galleries" />
              <SettingToggle label="Prompt history" desc="Store your prompt history for easy reuse" defaultChecked />
              <Box mt={4}>
                <Button
                  bg="transparent"
                  color="#FF4444"
                  border="1px solid #FF4444"
                  borderRadius="10px"
                  size="sm"
                  _hover={{ bg: 'rgba(255,68,68,0.1)' }}
                >
                  Delete All Data
                </Button>
              </Box>
            </Box>
          </Box>
        );

      case 'apikeys':
        return (
          <Box>
            <Heading size="md" color="#F4F7F0" mb={1}>API Keys</Heading>
            <Text color="#A5B1A7" fontSize="sm" mb={6}>Manage your API keys for programmatic access</Text>
            <Box bg="#111713" borderRadius="16px" border="1px solid #2A3A2C" p={6}>
              {[
                { name: 'Production Key', key: 'img_prod_sk_***...4f9a', created: 'Oct 15, 2026', lastUsed: '2 hours ago' },
                { name: 'Development Key', key: 'img_dev_sk_***...b2c1', created: 'Sep 3, 2026', lastUsed: '5 days ago' },
              ].map((apiKey, i) => (
                <Box
                  key={i}
                  py={4}
                  borderBottom={i === 0 ? '1px solid #2A3A2C' : 'none'}
                >
                  <Flex justify="space-between" align="center">
                    <Box>
                      <Text color="#F4F7F0" fontSize="sm" fontWeight={600}>{apiKey.name}</Text>
                      <Text color="#A5B1A7" fontSize="xs" fontFamily="mono" mt={1}>{apiKey.key}</Text>
                      <Flex gap={4} mt={1}>
                        <Text color="#A5B1A7" fontSize="xs">Created: {apiKey.created}</Text>
                        <Text color="#A5B1A7" fontSize="xs">Last used: {apiKey.lastUsed}</Text>
                      </Flex>
                    </Box>
                    <Flex gap={2}>
                      <Button
                        size="xs"
                        bg="transparent"
                        color="#A5B1A7"
                        border="1px solid #2A3A2C"
                        borderRadius="6px"
                        _hover={{ bg: '#1A2A1C', color: '#F4F7F0' }}
                      >
                        Copy
                      </Button>
                      <Button
                        size="xs"
                        bg="transparent"
                        color="#FF4444"
                        border="1px solid rgba(255,68,68,0.3)"
                        borderRadius="6px"
                        _hover={{ bg: 'rgba(255,68,68,0.1)' }}
                      >
                        Revoke
                      </Button>
                    </Flex>
                  </Flex>
                </Box>
              ))}
              <Button
                mt={4}
                bg="#B7FF35"
                color="#080B0A"
                borderRadius="10px"
                fontWeight={700}
                size="sm"
                _hover={{ bg: '#8DDB39' }}
              >
                + Generate New Key
              </Button>
            </Box>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <WorkspaceLayout>
      <Box p={8} minH="100vh" bg="#080B0A">
        <Heading size="lg" color="#F4F7F0" fontWeight={700} mb={1}>
          Settings
        </Heading>
        <Text color="#A5B1A7" fontSize="sm" mb={8}>
          Manage your profile, preferences, and account settings
        </Text>

        <Flex gap={8}>
          {/* Left Navigation */}
          <Box
            w="220px"
            flexShrink={0}
            bg="#111713"
            borderRadius="16px"
            border="1px solid #2A3A2C"
            p={3}
            position="sticky"
            top="32px"
            alignSelf="flex-start"
          >
            {NAV_ITEMS.map((item) => (
              <Box
                key={item.key}
                as="button"
                display="flex"
                alignItems="center"
                gap={3}
                w="100%"
                px={3}
                py={2.5}
                borderRadius="10px"
                bg={activeSection === item.key ? 'rgba(183,255,53,0.1)' : 'transparent'}
                color={activeSection === item.key ? '#B7FF35' : '#A5B1A7'}
                fontWeight={activeSection === item.key ? 600 : 400}
                fontSize="sm"
                cursor="pointer"
                _hover={{
                  bg: activeSection === item.key ? 'rgba(183,255,53,0.1)' : '#1A2A1C',
                  color: activeSection === item.key ? '#B7FF35' : '#F4F7F0',
                }}
                transition="all 0.2s ease"
                textAlign="left"
                onClick={() => setActiveSection(item.key)}
              >
                {item.icon}
                {item.label}
              </Box>
            ))}
          </Box>

          {/* Content Area */}
          <Box flex={1} minW={0}>
            {renderContent()}
          </Box>
        </Flex>
      </Box>
    </WorkspaceLayout>
  );
};

const Grid: React.FC<{ gap: number; children: React.ReactNode }> = ({ gap, children }) => (
  <Box sx={{ display: 'grid', gap: `${gap * 4}px` }}>
    {children}
  </Box>
);

export default ProfileSettings;
