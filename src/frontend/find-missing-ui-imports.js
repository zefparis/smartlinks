#!/usr/bin/env node

/**
 * Script d'audit des composants UI
 * Détecte tous les imports de composants UI et vérifie leur existence
 */

const fs = require('fs');
const path = require('path');

// Configuration
const srcDir = path.join(__dirname, 'src');
const uiComponentsDir = path.join(srcDir, 'components', 'ui');

// Liste des composants shadcn-ui disponibles
const shadcnComponents = [
  'accordion', 'alert', 'alert-dialog', 'aspect-ratio', 'avatar',
  'badge', 'breadcrumb', 'button', 'calendar', 'card', 'carousel',
  'checkbox', 'collapsible', 'command', 'context-menu', 'dialog',
  'drawer', 'dropdown-menu', 'form', 'hover-card', 'input', 'label',
  'menubar', 'navigation-menu', 'pagination', 'popover', 'progress',
  'radio-group', 'resizable', 'scroll-area', 'select', 'separator',
  'sheet', 'skeleton', 'slider', 'sonner', 'switch', 'table', 'tabs',
  'textarea', 'toast', 'toaster', 'toggle', 'toggle-group', 'tooltip'
];

// Fonction pour scanner récursivement les fichiers
function scanDirectory(dir, fileList = []) {
  const files = fs.readdirSync(dir);
  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    if (stat.isDirectory() && !file.includes('node_modules') && !file.startsWith('.')) {
      scanDirectory(filePath, fileList);
    } else if (stat.isFile() && /\.(tsx?|jsx?)$/.test(file)) {
      fileList.push(filePath);
    }
  });
  return fileList;
}

// Fonction pour extraire les imports de composants UI
function extractUIImports(content) {
  const imports = new Set();
  
  // Pattern pour les imports de @/components/ui/
  const importRegex = /from\s+['"](?:@\/components\/ui\/|\.\.\/ui\/|\.\.\/\.\.\/components\/ui\/|\.\/components\/ui\/)([^'"]+)['"]/g;
  let match;
  
  while ((match = importRegex.exec(content)) !== null) {
    imports.add(match[1]);
  }
  
  // Pattern pour les imports destructurés
  const destructuredRegex = /import\s+\{([^}]+)\}\s+from\s+['"](?:@\/components\/ui\/|\.\.\/ui\/|\.\.\/\.\.\/components\/ui\/|\.\/components\/ui\/)([^'"]+)['"]/g;
  
  content.replace(destructuredRegex, (fullMatch, components, file) => {
    imports.add(file);
    return fullMatch;
  });
  
  return Array.from(imports);
}

// Fonction principale
function auditUIComponents() {
  console.log('🔍 Audit des composants UI\n');
  console.log('📁 Dossier source:', srcDir);
  console.log('📁 Dossier UI:', uiComponentsDir);
  console.log('=' .repeat(60));
  
  // 1. Scanner tous les fichiers
  console.log('\n📂 Scan des fichiers...');
  const files = scanDirectory(srcDir);
  console.log(`✅ ${files.length} fichiers trouvés`);
  
  // 2. Extraire tous les imports UI
  console.log('\n🔎 Extraction des imports UI...');
  const allImports = new Set();
  const importsByFile = {};
  
  files.forEach(file => {
    const content = fs.readFileSync(file, 'utf8');
    const imports = extractUIImports(content);
    if (imports.length > 0) {
      imports.forEach(imp => allImports.add(imp));
      importsByFile[file] = imports;
    }
  });
  
  const importedComponents = Array.from(allImports).sort();
  console.log(`✅ ${importedComponents.length} composants UI importés`);
  
  // 3. Vérifier l'existence des composants
  console.log('\n🔍 Vérification de l'existence des composants...');
  const existingComponents = [];
  const missingComponents = [];
  
  importedComponents.forEach(component => {
    const componentPath = path.join(uiComponentsDir, `${component}.tsx`);
    const componentPathJs = path.join(uiComponentsDir, `${component}.jsx`);
    const componentPathTs = path.join(uiComponentsDir, `${component}.ts`);
    const componentPathIndex = path.join(uiComponentsDir, component, 'index.tsx');
    
    if (fs.existsSync(componentPath) || 
        fs.existsSync(componentPathJs) || 
        fs.existsSync(componentPathTs) ||
        fs.existsSync(componentPathIndex)) {
      existingComponents.push(component);
    } else {
      missingComponents.push(component);
    }
  });
  
  // 4. Afficher le rapport
  console.log('\n' + '=' .repeat(60));
  console.log('📊 RAPPORT D\'AUDIT');
  console.log('=' .repeat(60));
  
  console.log('\n✅ Composants présents (' + existingComponents.length + '):');
  if (existingComponents.length > 0) {
    existingComponents.forEach(comp => console.log(`   ✓ ${comp}`));
  }
  
  console.log('\n❌ Composants manquants (' + missingComponents.length + '):');
  if (missingComponents.length > 0) {
    missingComponents.forEach(comp => console.log(`   ✗ ${comp}`));
  }
  
  // 5. Générer les commandes pour installer les composants manquants
  if (missingComponents.length > 0) {
    console.log('\n' + '=' .repeat(60));
    console.log('🔧 COMMANDES À EXÉCUTER');
    console.log('=' .repeat(60));
    
    const shadcnMissing = missingComponents.filter(comp => 
      shadcnComponents.includes(comp.replace('.tsx', '').replace('.jsx', ''))
    );
    
    const customMissing = missingComponents.filter(comp => 
      !shadcnComponents.includes(comp.replace('.tsx', '').replace('.jsx', ''))
    );
    
    if (shadcnMissing.length > 0) {
      console.log('\n📦 Composants shadcn-ui à installer:');
      shadcnMissing.forEach(comp => {
        const componentName = comp.replace('.tsx', '').replace('.jsx', '');
        console.log(`   npx shadcn-ui@latest add ${componentName}`);
      });
    }
    
    if (customMissing.length > 0) {
      console.log('\n⚠️ Composants custom à créer manuellement:');
      customMissing.forEach(comp => {
        console.log(`   - ${comp}`);
      });
    }
    
    // Script batch pour installer tous les composants shadcn
    if (shadcnMissing.length > 0) {
      const batchCommands = shadcnMissing.map(comp => 
        `npx shadcn-ui@latest add ${comp.replace('.tsx', '').replace('.jsx', '')}`
      ).join(' && ');
      
      console.log('\n🚀 Commande batch pour installer tous les composants shadcn:');
      console.log(`   ${batchCommands}`);
    }
  }
  
  // 6. Créer un fichier de rapport
  const report = {
    timestamp: new Date().toISOString(),
    stats: {
      totalFiles: files.length,
      totalImports: importedComponents.length,
      existing: existingComponents.length,
      missing: missingComponents.length
    },
    components: {
      existing: existingComponents,
      missing: missingComponents
    },
    importsByFile: Object.fromEntries(
      Object.entries(importsByFile).map(([file, imports]) => [
        path.relative(srcDir, file),
        imports
      ])
    )
  };
  
  const reportPath = path.join(__dirname, 'ui-audit-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(`\n📄 Rapport sauvegardé dans: ${reportPath}`);
  
  // Retour du code de sortie
  process.exit(missingComponents.length > 0 ? 1 : 0);
}

// Exécution
try {
  auditUIComponents();
} catch (error) {
  console.error('❌ Erreur:', error.message);
  process.exit(1);
}
