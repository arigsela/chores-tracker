#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// App Icon configuration for iOS
const iosIconSizes = [
  { size: 20, scale: 2, idiom: 'iphone', filename: 'Icon-20@2x.png' },
  { size: 20, scale: 3, idiom: 'iphone', filename: 'Icon-20@3x.png' },
  { size: 29, scale: 2, idiom: 'iphone', filename: 'Icon-29@2x.png' },
  { size: 29, scale: 3, idiom: 'iphone', filename: 'Icon-29@3x.png' },
  { size: 40, scale: 2, idiom: 'iphone', filename: 'Icon-40@2x.png' },
  { size: 40, scale: 3, idiom: 'iphone', filename: 'Icon-40@3x.png' },
  { size: 60, scale: 2, idiom: 'iphone', filename: 'Icon-60@2x.png' },
  { size: 60, scale: 3, idiom: 'iphone', filename: 'Icon-60@3x.png' },
  { size: 1024, scale: 1, idiom: 'ios-marketing', filename: 'Icon-1024.png' },
];

// Create a simple app icon using Canvas (you'll need to install canvas package for this to work)
// For now, let's create the JSON configuration
const contentsJson = {
  images: iosIconSizes.map(({ size, scale, idiom, filename }) => ({
    size: `${size}x${size}`,
    idiom,
    filename,
    scale: `${scale}x`,
  })),
  info: {
    version: 1,
    author: 'xcode',
  },
};

const outputPath = path.join(__dirname, '../ios/ChoresTrackerMobile/Images.xcassets/AppIcon.appiconset/Contents.json');
fs.writeFileSync(outputPath, JSON.stringify(contentsJson, null, 2));

console.log('App icon configuration generated successfully!');
console.log('Note: You still need to generate the actual PNG files using a design tool.');
console.log('\nRequired icon sizes:');
iosIconSizes.forEach(({ size, scale, filename }) => {
  const actualSize = size * scale;
  console.log(`- ${filename}: ${actualSize}x${actualSize}px`);
});