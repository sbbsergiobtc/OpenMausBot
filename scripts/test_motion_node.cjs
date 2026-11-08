// Test Motion.animate return value
const fs = require('fs');
const https = require('https');

https.get('https://cdn.jsdelivr.net/npm/motion@11.11.17/dist/motion.js', (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    // evaluate in sandbox
    const context = { globalThis: {}, self: {}, window: {} };
    const fn = new Function('globalThis', 'self', 'window', data);
    fn(context.globalThis, context.self, context.window);
    const Motion = context.globalThis.Motion || context.window.Motion;
    console.log('Motion object keys:', Object.keys(Motion || {}));
    
    // Create dummy element
    const dummyEl = {
      style: {},
      getBoundingClientRect: () => ({ left: 0, top: 0, width: 100, height: 100 })
    };
    try {
      const anim = Motion.animate(dummyEl, { opacity: 0 }, { duration: 0.1 });
      console.log('Animation returned:', anim);
      console.log('anim.finished:', anim ? anim.finished : 'none');
    } catch (e) {
      console.log('Error calling Motion.animate:', e.message);
    }
  });
});
