import { useRef, useEffect, useState } from 'react';
import * as PIXI from 'pixi.js';
import { Button } from '@rpg/ui';

export interface CartographerProps {
  gridSize?: number;
  onTokenMove?: (tokenId: string, x: number, y: number) => void;
}

export function Cartographer({ gridSize = 50, onTokenMove: _onTokenMove }: CartographerProps) {
  const canvasRef = useRef<HTMLDivElement>(null);
  const appRef = useRef<PIXI.Application | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    if (!canvasRef.current || isInitialized) return;

    const initPixi = async () => {
      const app = new PIXI.Application({
        width: canvasRef.current!.clientWidth || 800,
        height: canvasRef.current!.clientHeight || 600,
        backgroundColor: 0x2c3e50,
        antialias: true,
      });
      
      // app.init() is v8, we are on v7
      // await app.init();

      canvasRef.current!.appendChild(app.view as unknown as Node);
      appRef.current = app;

      // Create grid
      const gridGraphics = new PIXI.Graphics();
      gridGraphics.lineStyle(1, 0x34495e, 0.5);

      const width = app.screen.width;
      const height = app.screen.height;

      // Vertical lines
      for (let x = 0; x <= width; x += gridSize) {
        gridGraphics.moveTo(x, 0);
        gridGraphics.lineTo(x, height);
      }

      // Horizontal lines
      for (let y = 0; y <= height; y += gridSize) {
        gridGraphics.moveTo(0, y);
        gridGraphics.lineTo(width, y);
      }

      app.stage.addChild(gridGraphics);

      // Handle window resize
      const handleResize = () => {
        if (app && canvasRef.current) {
          app.renderer.resize(
            canvasRef.current.clientWidth,
            canvasRef.current.clientHeight
          );
        }
      };

      window.addEventListener('resize', handleResize);
      setIsInitialized(true);

      return () => {
        window.removeEventListener('resize', handleResize);
        app.destroy(true);
      };
    };

    initPixi();
  }, [gridSize, isInitialized]);

  return (
    <div className="h-full w-full flex flex-col">
      <div className="p-2 border-b flex items-center gap-2">
        <Button size="sm" variant="outline">
          Grid: {gridSize}px
        </Button>
        <Button size="sm" variant="outline">
          Pan
        </Button>
        <Button size="sm" variant="outline">
          Zoom
        </Button>
      </div>
      <div ref={canvasRef} className="flex-1 w-full" />
    </div>
  );
}

