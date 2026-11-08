import http from 'http';
import https from 'https';

// Let's inspect the code of Motion.animate in motion.js
https.get('https://cdn.jsdelivr.net/npm/motion@11.11.17/dist/motion.js', (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    // Find animate function definition
    const match = data.match(/function animate\([^)]*\)\s*\{[^}]*\}/);
    console.log("animate definition snippet:");
    const idx = data.indexOf('function animate(');
    console.log(data.slice(idx, idx + 500));
  });
});
