# Script pour démarrer le serveur avec une journalisation complète

# Configuration
$logDir = "logs"
$currentDate = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = "${logDir}/server_${currentDate}.log"
$errorLogFile = "${logDir}/error_${currentDate}.log"

# Créer le répertoire de logs s'il n'existe pas
if (-not (Test-Path -Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
    Write-Host "Création du répertoire de logs: $logDir"
}

# Afficher les informations de démarrage
Write-Host "=== Démarrage du serveur FastAPI ===" -ForegroundColor Cyan
Write-Host "Date et heure: $(Get-Date)"
Write-Host "Répertoire de travail: $PWD"
Write-Host "Fichier de log: $PWD\$logFile"
Write-Host "Fichier d'erreurs: $PWD\$errorLogFile"

# Définir les variables d'environnement
$env:PYTHONPATH = "$PWD\src"
$env:PYTHONUNBUFFERED = "1"

# Commande pour démarrer le serveur
$command = ".venv\Scripts\python.exe -m uvicorn soft.router:app --reload --host 0.0.0.0 --port 8000 --log-level debug"

# Afficher la commande exécutée
Write-Host "\nCommande exécutée:" -ForegroundColor Cyan
Write-Host $command

# Exécuter la commande avec redirection de la sortie
Write-Host "\nDémarrage du serveur... (Appuyez sur Ctrl+C pour arrêter)" -ForegroundColor Yellow

# Exécuter la commande avec redirection de la sortie
Start-Process -NoNewWindow -FilePath ".venv\Scripts\python.exe" `
    -ArgumentList "-m uvicorn soft.router:app --reload --host 0.0.0.0 --port 8000 --log-level debug" `
    -RedirectStandardOutput $logFile `
    -RedirectStandardError $errorLogFile

# Afficher les logs en temps réel
Get-Content -Path $logFile -Wait
