const fs = require('fs');
const path = require('path');

const uiDir = path.join(__dirname, 'src', 'components', 'ui');

// Liste des composants importés dans le projet (détectés manuellement)
const requiredComponents = [
  'alert',
  'badge', 
  'button',
  'calendar',
  'card',
  'date-range-picker',
  'dialog',
  'input',
  'label',
  'popover',
  'progress',
  'radio-group',
  'scroll-area',
  'select',
  'separator',
  'sheet',
  'skeleton',
  'slider',
  'switch',
  'table',
  'tabs',
  'textarea',
  'tooltip',
  'StatusIndicator'
];

console.log('Checking UI components...\n');

const existing = [];
const missing = [];

requiredComponents.forEach(comp => {
  const filePath = path.join(uiDir, `${comp}.tsx`);
  if (fs.existsSync(filePath)) {
    existing.push(comp);
    console.log(`✅ ${comp}`);
  } else {
    missing.push(comp);
    console.log(`❌ ${comp}`);
  }
});

console.log('\n' + '='.repeat(50));
console.log(`Total: ${requiredComponents.length}`);
console.log(`Existing: ${existing.length}`);
console.log(`Missing: ${missing.length}`);

if (missing.length > 0) {
  console.log('\n⚠️  Missing components:', missing.join(', '));
}
