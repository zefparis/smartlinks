#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de vérification des endpoints analytics SmartLinks
Teste tous les endpoints et vérifie que les données sont correctement retournées
"""

import sys
import os
import requests
import json
from pathlib import Path

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

BASE_URL = "http://localhost:8000/api/analytics"

def test_endpoint(endpoint, params=None):
    """Teste un endpoint et retourne le résultat"""
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return True, data
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except requests.exceptions.RequestException as e:
        return False, f"Erreur de connexion: {e}"

def main():
    print("🔍 VÉRIFICATION DES ENDPOINTS ANALYTICS")
    print("=" * 50)
    
    # Liste des endpoints à tester
    endpoints = [
        ("/health", None, "Health check"),
        ("/devices", None, "Device statistics"),
        ("/countries", {"days": 30, "limit": 10}, "Country statistics"),
        ("/clicks/history", {"days": 7}, "Click history"),
        ("/traffic-by-segment", {"days": 30, "limit": 20}, "Traffic by segment"),
    ]
    
    all_success = True
    
    for endpoint, params, description in endpoints:
        print(f"\n📊 Test: {description}")
        print(f"   Endpoint: {endpoint}")
        if params:
            print(f"   Params: {params}")
        
        success, result = test_endpoint(endpoint, params)
        
        if success:
            print("   ✅ Succès")
            
            # Afficher quelques statistiques selon l'endpoint
            if endpoint == "/health":
                db_stats = result.get("database", {})
                print(f"      Clics: {db_stats.get('clicks', 0):,}")
                print(f"      Conversions: {db_stats.get('conversions', 0):,}")
                print(f"      Segments: {db_stats.get('segments', 0)}")
                
            elif endpoint == "/devices":
                devices = result.get("devices", [])
                total_clicks = result.get("total_clicks", 0)
                print(f"      Devices trouvés: {len(devices)}")
                print(f"      Total clics: {total_clicks:,}")
                if devices:
                    top_device = devices[0]
                    print(f"      Top device: {top_device.get('device')} ({top_device.get('clicks', 0):,} clics)")
                    
            elif endpoint == "/countries":
                countries = result.get("countries", [])
                print(f"      Pays trouvés: {len(countries)}")
                if countries:
                    top_country = countries[0]
                    print(f"      Top pays: {top_country.get('country')} ({top_country.get('clicks', 0):,} clics)")
                    
            elif endpoint == "/clicks/history":
                history = result.get("history", [])
                total_clicks = result.get("total_clicks", 0)
                print(f"      Jours avec données: {len(history)}")
                print(f"      Total clics: {total_clicks:,}")
                
            elif endpoint == "/traffic-by-segment":
                segments = result.get("segments", [])
                total_clicks = result.get("totals", {}).get("clicks", 0)
                print(f"      Segments trouvés: {len(segments)}")
                print(f"      Total clics: {total_clicks:,}")
                if segments:
                    top_segment = segments[0]
                    print(f"      Top segment: {top_segment.get('segment_id')} ({top_segment.get('clicks', 0):,} clics)")
        else:
            print(f"   ❌ Échec: {result}")
            all_success = False
    
    print("\n" + "=" * 50)
    if all_success:
        print("✅ TOUS LES ENDPOINTS FONCTIONNENT CORRECTEMENT")
        print("\n🌐 URLs à tester dans le navigateur:")
        print("   Frontend: http://localhost:3000/analytics")
        print("   API Docs: http://localhost:8000/docs")
        print("   Health: http://localhost:8000/api/analytics/health")
    else:
        print("❌ CERTAINS ENDPOINTS ONT DES PROBLÈMES")
        print("\n🔧 Actions possibles:")
        print("   1. Vérifier que le backend tourne: python main.py")
        print("   2. Regénérer les données: scripts\\seed.bat --clean")
        print("   3. Vérifier les logs: scripts\\debug.bat")
    
    return all_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
