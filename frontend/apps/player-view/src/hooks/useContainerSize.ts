import { useEffect, useState, RefObject } from "react";

export interface ContainerSize {
  width: number;
  height: number;
  isPortrait: boolean;
  isLandscape: boolean;
}

/**
 * Hook that tracks container dimensions using ResizeObserver.
 * Useful for responsive layouts that need to adapt based on container size.
 */
export function useContainerSize(ref: RefObject<HTMLElement | null>): ContainerSize {
  const [size, setSize] = useState<ContainerSize>({
    width: 0,
    height: 0,
    isPortrait: false,
    isLandscape: true,
  });

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const updateSize = () => {
      const { width, height } = element.getBoundingClientRect();
      setSize({
        width,
        height,
        isPortrait: height > width,
        isLandscape: width >= height,
      });
    };

    // Initial measurement
    updateSize();

    const resizeObserver = new ResizeObserver(() => {
      updateSize();
    });

    resizeObserver.observe(element);

    return () => {
      resizeObserver.disconnect();
    };
  }, [ref]);

  return size;
}
