#!/usr/bin/env python3

import sys
import os
import argparse
import logging
import schedule
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scraper import FoodIndustryNewsScraper
from bulletin_generator import BulletinGenerator
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration d'analyse avec validation
def load_analysis_config():
    """Charger la configuration d'analyse avec validation et fallback"""
    config = None
    config_source = "default"
    
    # Essayer d'abord config_openrouter
    try:
        from config_openrouter import get_analysis_config
        config = get_analysis_config()
        config_source = "openrouter"
        logger.info(f"Configuration OpenRouter chargée: modèle {config.get('openrouter_model', 'N/A')}")
    except ImportError as e:
        logger.warning(f"config_openrouter.py introuvable: {e}")
    except Exception as e:
        logger.error(f"Erreur lors du chargement de config_openrouter: {e}")
    
    # Fallback sur config.py
    if config is None:
        try:
            if hasattr(config, 'ANALYSIS_CONFIG'):
                config = config.ANALYSIS_CONFIG
                config_source = "config.py"
                logger.info("Configuration d'analyse chargée depuis config.py")
        except Exception as e:
            logger.warning(f"Erreur config.py: {e}")
    
    # Validation de la configuration
    if config:
        required_keys = ['mode', 'enable_bm25']
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            logger.warning(f"Clés manquantes dans la configuration {config_source}: {missing_keys}")
        else:
            logger.info(f"Configuration {config_source} validée avec succès")
    else:
        logger.warning("Aucune configuration d'analyse disponible, mode basique activé")
    
    return config, config_source

ANALYSIS_CONFIG, CONFIG_SOURCE = load_analysis_config()

class FLBNewsApp:
    def __init__(self):
        # Configuration avec validation
        analysis_config = ANALYSIS_CONFIG or getattr(config, 'ANALYSIS_CONFIG', None)
        
        if analysis_config is None:
            logger.warning("Mode de compatibilité: utilisation du scoring basique seulement")
        else:
            logger.info(f"Mode d'analyse: {analysis_config.get('mode', 'non spécifié')} (source: {CONFIG_SOURCE})")
        
        # Validation des dépendances
        self._validate_dependencies(analysis_config)
        
        # Initialiser le scraper avec configuration validée
        try:
            self.scraper = FoodIndustryNewsScraper(
                config.NEWS_SOURCES,
                keywords_config=getattr(config, 'RELEVANCE_KEYWORDS', None),
                analysis_config=analysis_config,
                bulletin_config=config.BULLETIN_CONFIG
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du scraper: {e}")
            raise
        
        # Initialiser le générateur de bulletin
        try:
            self.generator = BulletinGenerator(config.BULLETIN_CONFIG.get('template_path'))
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du générateur: {e}")
            raise
    
    def _validate_dependencies(self, analysis_config):
        """Valider les dépendances selon la configuration"""
        if not analysis_config:
            return
        
        # Vérifier BM25
        if analysis_config.get('enable_bm25', False):
            try:
                import rank_bm25
                logger.info("✓ BM25 disponible")
            except ImportError:
                logger.warning("✗ rank-bm25 non installé, scoring de base utilisé")
        
        # Vérifier Ollama
        if analysis_config.get('enable_ollama', False):
            try:
                import ollama
                logger.info("✓ Ollama client disponible")
            except ImportError:
                logger.warning("✗ ollama non installé, analyse locale désactivée")
        
        # Vérifier OpenRouter
        if analysis_config.get('enable_openrouter', False):
            api_key = analysis_config.get('openrouter_api_key') or os.getenv('OPENROUTER_API_KEY')
            if api_key:
                logger.info("✓ Clé OpenRouter présente")
            else:
                logger.warning("✗ Clé OpenRouter manquante, analyse cloud désactivée")
        
    def run_bulletin_generation(self):
        logger.info("Début de la génération du bulletin...")
        
        try:
            logger.info(f"Recherche de nouvelles des {config.BULLETIN_CONFIG['days_to_scrape']} derniers jours...")
            news_items = self.scraper.scrape_all_sources(
                days_back=config.BULLETIN_CONFIG['days_to_scrape']
            )
            
            if not news_items:
                logger.warning("Aucune nouvelle trouvée pour cette période")
                return None
                
            logger.info(f"{len(news_items)} nouvelles pertinentes trouvées")
            
            news_items = news_items[:config.BULLETIN_CONFIG['max_articles']]
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"bulletin_flb_{timestamp}.html"
            output_path = os.path.join(config.BULLETIN_CONFIG['output_directory'], filename)
            
            bulletin_html = self.generator.generate_bulletin(news_items, output_path)
            logger.info(f"Bulletin généré: {output_path}")
            
            return {
                'html': bulletin_html,
                'path': output_path,
                'news_items': news_items
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du bulletin: {str(e)}")
            raise
    
    def send_email(self, bulletin_data):
        if not config.EMAIL_CONFIG['sender_email'] or not config.EMAIL_CONFIG['recipient_emails']:
            logger.warning("Configuration email incomplète, envoi ignoré")
            return False
            
        try:
            email_html = self.generator.generate_email_version(bulletin_data['news_items'])
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Bulletin FLB - {datetime.now().strftime('%d %B %Y')}"
            msg['From'] = config.EMAIL_CONFIG['sender_email']
            msg['To'] = ', '.join(config.EMAIL_CONFIG['recipient_emails'])
            
            html_part = MIMEText(email_html, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(config.EMAIL_CONFIG['smtp_server'], config.EMAIL_CONFIG['smtp_port']) as server:
                server.starttls()
                server.login(
                    config.EMAIL_CONFIG['sender_email'],
                    config.EMAIL_CONFIG['sender_password']
                )
                server.send_message(msg)
                
            logger.info(f"Email envoyé à {len(config.EMAIL_CONFIG['recipient_emails'])} destinataires")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email: {str(e)}")
            return False
    
    def sync_to_sharepoint(self, bulletin_path):
        if not config.SHAREPOINT_CONFIG['site_url']:
            logger.warning("Configuration SharePoint incomplète, synchronisation ignorée")
            return False
            
        try:
            logger.info("Synchronisation SharePoint non implémentée dans cette version")
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation SharePoint: {str(e)}")
            return False
    
    def scheduled_task(self):
        logger.info("Exécution de la tâche planifiée...")
        bulletin_data = self.run_bulletin_generation()
        
        if bulletin_data:
            self.send_email(bulletin_data)
            self.sync_to_sharepoint(bulletin_data['path'])
            
        logger.info("Tâche planifiée terminée")
    
    def start_scheduler(self):
        if not config.SCHEDULE_CONFIG['enabled']:
            logger.info("Planificateur désactivé")
            return
            
        schedule_time = config.SCHEDULE_CONFIG['time']
        schedule_days = config.SCHEDULE_CONFIG['days']
        
        for day in schedule_days:
            if day.lower() == 'monday':
                schedule.every().monday.at(schedule_time).do(self.scheduled_task)
            elif day.lower() == 'tuesday':
                schedule.every().tuesday.at(schedule_time).do(self.scheduled_task)
            elif day.lower() == 'wednesday':
                schedule.every().wednesday.at(schedule_time).do(self.scheduled_task)
            elif day.lower() == 'thursday':
                schedule.every().thursday.at(schedule_time).do(self.scheduled_task)
            elif day.lower() == 'friday':
                schedule.every().friday.at(schedule_time).do(self.scheduled_task)
                
        logger.info(f"Planificateur activé: {', '.join(schedule_days)} à {schedule_time}")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

def main():
    parser = argparse.ArgumentParser(
        description="FLB News - Générateur de bulletin de nouvelles de l'industrie alimentaire"
    )
    parser.add_argument(
        '--run-now',
        action='store_true',
        help="Générer le bulletin immédiatement"
    )
    parser.add_argument(
        '--send-email',
        action='store_true',
        help="Envoyer le bulletin par email après génération"
    )
    parser.add_argument(
        '--sync-sharepoint',
        action='store_true',
        help="Synchroniser le bulletin vers SharePoint"
    )
    parser.add_argument(
        '--schedule',
        action='store_true',
        help="Démarrer le planificateur selon la configuration"
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help="Nombre de jours à rechercher (défaut: 7)"
    )
    
    args = parser.parse_args()
    
    app = FLBNewsApp()
    
    if args.days != 7:
        config.BULLETIN_CONFIG['days_to_scrape'] = args.days
    
    if args.schedule:
        logger.info("Démarrage du planificateur...")
        app.start_scheduler()
    elif args.run_now or not any([args.schedule]):
        bulletin_data = app.run_bulletin_generation()
        
        if bulletin_data:
            print(f"\n✅ Bulletin généré avec succès")
            print(f"📁 Emplacement : {bulletin_data['path']}")
            print(f"📰 Nombre d'articles : {len(bulletin_data['news_items'])}")
            
            if args.send_email:
                if app.send_email(bulletin_data):
                    print("📧 Email envoyé avec succès!")
                else:
                    print("❌ Échec de l'envoi de l'email")
                    
            if args.sync_sharepoint:
                if app.sync_to_sharepoint(bulletin_data['path']):
                    print("☁️ Synchronisé vers SharePoint!")
                else:
                    print("❌ Échec de la synchronisation SharePoint")
        else:
            print("❌ Aucune nouvelle trouvée ou erreur lors de la génération")
            
    else:
        parser.print_help()

if __name__ == "__main__":
    main()