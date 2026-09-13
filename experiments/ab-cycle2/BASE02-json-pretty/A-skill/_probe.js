const fs = require('fs');
const out = [];
out.push('node version: ' + process.version);
out.push('platform: ' + process.platform);
fs.writeFileSync(__dirname + '/_probe_out.txt', out.join('\n'), 'utf8');
