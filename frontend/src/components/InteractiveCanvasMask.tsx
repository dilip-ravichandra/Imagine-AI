import React, { useRef, useState, useEffect } from 'react';
import {
  Box,
  Flex,
  Text,
  Button,
  HStack,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  Badge,
  IconButton,
  Tooltip,
} from '@chakra-ui/react';
import { FiEdit2, FiCircle, FiSquare, FiTrash2, FiRotateCcw } from 'react-icons/fi';

interface InteractiveCanvasMaskProps {
  imageUrl: string;
  onMaskChange?: (hasMask: boolean, maskDataUrl?: string) => void;
}

export const InteractiveCanvasMask: React.FC<InteractiveCanvasMaskProps> = ({
  imageUrl,
  onMaskChange,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [tool, setTool] = useState<'circle' | 'brush' | 'box'>('circle');
  const [brushSize, setBrushSize] = useState(28);
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPos, setStartPos] = useState<{ x: number; y: number } | null>(null);
  const [hasMask, setHasMask] = useState(false);
  const [maskCount, setMaskCount] = useState(0);

  // Background image ref
  const imgRef = useRef<HTMLImageElement | null>(null);

  // Initialize canvas with image
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new window.Image();
    img.crossOrigin = 'anonymous';
    img.src = imageUrl;
    img.onload = () => {
      imgRef.current = img;
      // Draw background image
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      setHasMask(false);
      setMaskCount(0);
      onMaskChange?.(false);
    };
  }, [imageUrl]);

  // Redraw the base image + existing mask
  const redrawBase = () => {
    const canvas = canvasRef.current;
    if (!canvas || !imgRef.current) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(imgRef.current, 0, 0, canvas.width, canvas.height);
  };

  const getCanvasCoords = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY,
    };
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const { x, y } = getCanvasCoords(e);
    setIsDrawing(true);
    setStartPos({ x, y });

    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!ctx) return;

    if (tool === 'brush') {
      ctx.beginPath();
      ctx.arc(x, y, brushSize / 2, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(183, 255, 53, 0.45)';
      ctx.fill();
      ctx.beginPath();
      ctx.moveTo(x, y);
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !startPos) return;
    const { x, y } = getCanvasCoords(e);
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!ctx) return;

    if (tool === 'brush') {
      ctx.strokeStyle = 'rgba(183, 255, 53, 0.45)';
      ctx.lineWidth = brushSize;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.lineTo(x, y);
      ctx.stroke();
    } else if (tool === 'circle') {
      // Circle / Ellipse drag preview
      redrawBase();
      ctx.save();
      const radiusX = Math.abs(x - startPos.x) / 2;
      const radiusY = Math.abs(y - startPos.y) / 2;
      const centerX = Math.min(startPos.x, x) + radiusX;
      const centerY = Math.min(startPos.y, y) + radiusY;

      ctx.beginPath();
      ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, 0, 2 * Math.PI);
      ctx.fillStyle = 'rgba(183, 255, 53, 0.4)';
      ctx.fill();
      ctx.lineWidth = 2.5;
      ctx.setLineDash([6, 4]);
      ctx.strokeStyle = '#B7FF35';
      ctx.stroke();
      ctx.restore();
    } else if (tool === 'box') {
      redrawBase();
      ctx.save();
      const width = x - startPos.x;
      const height = y - startPos.y;
      ctx.fillStyle = 'rgba(183, 255, 53, 0.4)';
      ctx.fillRect(startPos.x, startPos.y, width, height);
      ctx.lineWidth = 2.5;
      ctx.setLineDash([6, 4]);
      ctx.strokeStyle = '#B7FF35';
      ctx.strokeRect(startPos.x, startPos.y, width, height);
      ctx.restore();
    }
  };

  const handleMouseUp = () => {
    if (!isDrawing) return;
    setIsDrawing(false);
    setStartPos(null);
    setHasMask(true);
    setMaskCount((prev) => prev + 1);

    const canvas = canvasRef.current;
    if (canvas && onMaskChange) {
      onMaskChange(true, canvas.toDataURL());
    }
  };

  const handleClearMask = () => {
    const canvas = canvasRef.current;
    if (!canvas || !imgRef.current) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(imgRef.current, 0, 0, canvas.width, canvas.height);
    setHasMask(false);
    setMaskCount(0);
    onMaskChange?.(false);
  };

  // Quick preset masks (e.g. Center Subject, Sky/Top, Bottom Half)
  const applyPresetMask = (preset: 'center' | 'top' | 'bottom') => {
    const canvas = canvasRef.current;
    if (!canvas || !imgRef.current) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    redrawBase();

    ctx.save();
    ctx.fillStyle = 'rgba(183, 255, 53, 0.42)';
    ctx.lineWidth = 2;
    ctx.setLineDash([6, 4]);
    ctx.strokeStyle = '#B7FF35';

    if (preset === 'center') {
      const cx = canvas.width / 2;
      const cy = canvas.height / 2;
      const rx = canvas.width * 0.28;
      const ry = canvas.height * 0.35;
      ctx.beginPath();
      ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    } else if (preset === 'top') {
      ctx.fillRect(0, 0, canvas.width, canvas.height * 0.45);
      ctx.strokeRect(0, 0, canvas.width, canvas.height * 0.45);
    } else if (preset === 'bottom') {
      ctx.fillRect(0, canvas.height * 0.55, canvas.width, canvas.height * 0.45);
      ctx.strokeRect(0, canvas.height * 0.55, canvas.width, canvas.height * 0.45);
    }
    ctx.restore();

    setHasMask(true);
    setMaskCount(1);
    onMaskChange?.(true, canvas.toDataURL());
  };

  return (
    <Box bg="#0D120E" border="1px solid #2A3A2C" borderRadius="14px" p={3.5}>
      {/* Top Controls Toolbar */}
      <Flex justify="space-between" align="center" mb={3} wrap="wrap" gap={2}>
        <HStack spacing={1.5}>
          <Tooltip label="Circle / Oval Region Tool (Click & drag to circle region)">
            <Button
              size="xs"
              bg={tool === 'circle' ? '#B7FF35' : '#182019'}
              color={tool === 'circle' ? '#080B0A' : '#A5B1A7'}
              border="1px solid"
              borderColor={tool === 'circle' ? '#B7FF35' : '#2A3A2C'}
              _hover={{ borderColor: '#B7FF35' }}
              leftIcon={<FiCircle size={12} />}
              onClick={() => setTool('circle')}
              fontWeight="bold"
            >
              Circle Region
            </Button>
          </Tooltip>

          <Tooltip label="Brush Mask Tool (Paint freehand over region)">
            <Button
              size="xs"
              bg={tool === 'brush' ? '#B7FF35' : '#182019'}
              color={tool === 'brush' ? '#080B0A' : '#A5B1A7'}
              border="1px solid"
              borderColor={tool === 'brush' ? '#B7FF35' : '#2A3A2C'}
              _hover={{ borderColor: '#B7FF35' }}
              leftIcon={<FiEdit2 size={12} />}
              onClick={() => setTool('brush')}
              fontWeight="bold"
            >
              Brush Mask
            </Button>
          </Tooltip>

          <Tooltip label="Box Selection Tool">
            <Button
              size="xs"
              bg={tool === 'box' ? '#B7FF35' : '#182019'}
              color={tool === 'box' ? '#080B0A' : '#A5B1A7'}
              border="1px solid"
              borderColor={tool === 'box' ? '#B7FF35' : '#2A3A2C'}
              _hover={{ borderColor: '#B7FF35' }}
              leftIcon={<FiSquare size={12} />}
              onClick={() => setTool('box')}
              fontWeight="bold"
            >
              Box Select
            </Button>
          </Tooltip>

          <Tooltip label="Clear Selection / Mask">
            <IconButton
              aria-label="Clear Mask"
              icon={<FiRotateCcw size={12} />}
              size="xs"
              variant="ghost"
              color="#FF4444"
              _hover={{ bg: '#182019' }}
              onClick={handleClearMask}
            />
          </Tooltip>
        </HStack>

        {/* Brush Size / Status */}
        <Flex align="center" gap={3}>
          {tool === 'brush' && (
            <Flex align="center" gap={2}>
              <Text fontSize="10px" color="#A5B1A7">Size: {brushSize}px</Text>
              <Slider
                aria-label="brush-size"
                value={brushSize}
                min={8}
                max={60}
                onChange={(val) => setBrushSize(val)}
                w="60px"
              >
                <SliderTrack bg="#182019">
                  <SliderFilledTrack bg="#B7FF35" />
                </SliderTrack>
                <SliderThumb boxSize={3} bg="#B7FF35" />
              </Slider>
            </Flex>
          )}

          <Badge
            bg={hasMask ? 'rgba(183,255,53,0.2)' : 'rgba(255,255,255,0.06)'}
            color={hasMask ? '#B7FF35' : '#6B7B6D'}
            fontSize="10px"
            px={2}
            py={0.5}
            borderRadius="full"
          >
            {hasMask ? `✓ Region Circled` : `Drag on image to circle region`}
          </Badge>
        </Flex>
      </Flex>

      {/* Preset quick selection pills */}
      <Flex align="center" gap={2} mb={3}>
        <Text fontSize="10px" color="#6B7B6D">Quick Presets:</Text>
        <Button size="xs" variant="ghost" color="#A5B1A7" fontSize="10px" h="20px" px={2} _hover={{ color: '#B7FF35', bg: '#182019' }} onClick={() => applyPresetMask('center')}>
          🎯 Center Subject
        </Button>
        <Button size="xs" variant="ghost" color="#A5B1A7" fontSize="10px" h="20px" px={2} _hover={{ color: '#B7FF35', bg: '#182019' }} onClick={() => applyPresetMask('top')}>
          ☁️ Sky / Background
        </Button>
        <Button size="xs" variant="ghost" color="#A5B1A7" fontSize="10px" h="20px" px={2} _hover={{ color: '#B7FF35', bg: '#182019' }} onClick={() => applyPresetMask('bottom')}>
          🌊 Ground / Foreground
        </Button>
      </Flex>

      {/* Canvas container */}
      <Box
        ref={containerRef}
        position="relative"
        borderRadius="10px"
        overflow="hidden"
        border="1px solid #2A3A2C"
        bg="#080B0A"
        display="flex"
        alignItems="center"
        justifyContent="center"
        cursor={tool === 'brush' ? 'crosshair' : 'crosshair'}
        userSelect="none"
      >
        <canvas
          ref={canvasRef}
          width={640}
          height={380}
          style={{
            maxWidth: '100%',
            height: 'auto',
            display: 'block',
          }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        />
      </Box>

      <Text fontSize="10px" color="#6B7B6D" textAlign="center" mt={2}>
        💡 Click and drag directly on the image to circle or brush the exact area you want recreated.
      </Text>
    </Box>
  );
};

export default InteractiveCanvasMask;
