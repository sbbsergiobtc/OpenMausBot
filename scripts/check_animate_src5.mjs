import https from 'https';

https.get('https://cdn.jsdelivr.net/npm/motion@11.11.17/dist/motion.js', (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    const idx = data.indexOf('t.animate=');
    console.log("t.animate= at:", idx);
    console.log(data.slice(idx - 100, idx + 300));
  });
});
