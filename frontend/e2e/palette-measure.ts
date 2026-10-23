export function measurePalette(): { bgLum: number; headingContrasts: number[] } {
  function parseRgb(color: string): [number, number, number] {
    const values = color.match(/[\d.]+/g);
    return values && values.length >= 3
      ? [Number(values[0]), Number(values[1]), Number(values[2])]
      : [0, 0, 0];
  }

  function luminance(rgb: [number, number, number]): number {
    const [r, g, b] = rgb.map((channel) => {
      const value = channel / 255;
      return value <= 0.03928 ? value / 12.92 : Math.pow((value + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  }

  function contrast(first: number, second: number): number {
    const lighter = Math.max(first, second);
    const darker = Math.min(first, second);
    return (lighter + 0.05) / (darker + 0.05);
  }

  function opaqueBackground(element: Element): string {
    let current: Element | null = element;
    while (current) {
      const background = window.getComputedStyle(current).backgroundColor;
      const alpha =
        background.match(/rgba\([^,]+,[^,]+,[^,]+,\s*([\d.]+)\s*\)$/)?.[1] ??
        background.match(/rgb\([^)]*\/\s*([\d.]+)\s*\)$/)?.[1];
      if (!background.includes("transparent") && (alpha === undefined || Number(alpha) === 1)) {
        return background;
      }
      current = current.parentElement;
    }
    return "rgb(255, 255, 255)";
  }

  const bgLum = luminance(parseRgb(opaqueBackground(document.body)));
  const headingContrasts = Array.from(document.querySelectorAll("h1, h2, h3"))
    .filter((heading) => !heading.closest('[aria-hidden="true"]'))
    .map((heading) => {
      const foreground = parseRgb(window.getComputedStyle(heading).color);
      const background = parseRgb(opaqueBackground(heading));
      return contrast(luminance(foreground), luminance(background));
    });

  return { bgLum, headingContrasts };
}
