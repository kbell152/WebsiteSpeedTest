#!/usr/local/bin/node
//'use strict';
// Import the 'fs' module to work with the filesystem
const fs = require('fs');

fs.readFile('file.json', 'utf8', (err, data) => {
    if (err) {
        console.error('Error reading file:', err);
        return;
    }

    const matches = [...data.matchAll(/"link":\s*"([^"]+)"/g)];
    if (matches.length > 0) {
        matches.forEach(match => {
            const cleanedLink = match[1].replace(/\\/g, ''); // Remove all backslashes
            console.log(cleanedLink);
        });
    } else {
        console.log('No "link" fields found.');
    }
});
