import https from 'https';

https.get('https://cdn.jsdelivr.net/npm/motion@11.11.17/dist/motion.js', (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    const idx = data.indexOf('fs=');
    console.log("fs= at:", idx);
    console.log(data.slice(idx - 50, idx + 400));
  });
});
