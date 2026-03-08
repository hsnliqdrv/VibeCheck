/**
 * Extract the dominant color from an image URL using Canvas API
 * @param {string} imageUrl - URL of the image
 * @returns {Promise<string>} - Hex color code (e.g., #FF5733)
 */
export async function extractDominantColor(imageUrl) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = "Anonymous";
    
    img.onload = () => {
      try {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        // Use smaller dimensions for faster processing
        const maxSize = 100;
        const scale = Math.min(maxSize / img.width, maxSize / img.height);
        canvas.width = img.width * scale;
        canvas.height = img.height * scale;
        
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const pixels = imageData.data;
        
        // Color buckets for clustering
        const colorMap = {};
        
        // Sample pixels (skip some for performance)
        for (let i = 0; i < pixels.length; i += 16) { // Sample every 4th pixel
          const r = pixels[i];
          const g = pixels[i + 1];
          const b = pixels[i + 2];
          const a = pixels[i + 3];
          
          // Skip transparent or very dark/bright pixels
          if (a < 128 || (r < 20 && g < 20 && b < 20) || (r > 235 && g > 235 && b > 235)) {
            continue;
          }
          
          // Quantize colors to reduce variation (round to nearest 32)
          const quantize = (val) => Math.round(val / 32) * 32;
          const key = `${quantize(r)},${quantize(g)},${quantize(b)}`;
          
          colorMap[key] = (colorMap[key] || 0) + 1;
        }
        
        // Find most frequent color
        let maxCount = 0;
        let dominantColor = null;
        
        for (const [color, count] of Object.entries(colorMap)) {
          if (count > maxCount) {
            maxCount = count;
            dominantColor = color;
          }
        }
        
        if (!dominantColor) {
          // Fallback to a default color
          resolve('#6366F1'); // Indigo-500
          return;
        }
        
        // Convert to hex
        const [r, g, b] = dominantColor.split(',').map(Number);
        const hex = `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`.toUpperCase();
        
        resolve(hex);
      } catch (error) {
        console.error('Error extracting color:', error);
        resolve('#6366F1'); // Fallback color
      }
    };
    
    img.onerror = () => {
      console.error('Failed to load image for color extraction');
      resolve('#6366F1'); // Fallback color
    };
    
    // Add timestamp to bypass cache
    const separator = imageUrl.includes('?') ? '&' : '?';
    img.src = `${imageUrl}${separator}_=${Date.now()}`;
  });
}
