import logging
from typing import Optional
import hashlib
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

try:
    import deepl
    DEEPL_AVAILABLE = True
except ImportError:
    DEEPL_AVAILABLE = False

logger = logging.getLogger(__name__)

class NewsTranslator:
    # Version du traducteur - changer pour invalider tout le cache
    TRANSLATOR_VERSION = "2.1.0"
    
    def __init__(self):
        self.cache_dir = os.path.join(os.path.dirname(__file__), '..', '.translation_cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Nettoyer le cache au démarrage + vérifier version
        self._cleanup_expired_cache()
        self._check_version_compatibility()
        
        # Charger les variables d'environnement
        load_dotenv()
        
        # Initialiser DeepL si disponible
        self.translator = None
        if DEEPL_AVAILABLE:
            api_key = os.getenv('DEEPL_API_KEY')
            if api_key:
                try:
                    self.translator = deepl.Translator(api_key)
                    # Test rapide pour vérifier que ça fonctionne
                    usage = self.translator.get_usage()
                    logger.info(f"DeepL initialisé avec succès - {usage.character.count}/{usage.character.limit} caractères utilisés ce mois")
                except Exception as e:
                    logger.warning(f"Impossible d'initialiser DeepL: {e}")
                    logger.warning("Utilisation de la traduction de base")
                    self.translator = None
            else:
                logger.warning("Clé API DeepL non trouvée dans .env")
        else:
            logger.warning("Module deepl non installé - utilisation de la traduction de base")
        
        # Dictionnaire de secours pour les termes spécifiques
        self.food_terms = {
            'supply chain': 'chaîne d\'approvisionnement',
            'food distribution': 'distribution alimentaire',
            'wholesale': 'vente en gros',
            'wholesaler': 'grossiste',
            'retailer': 'détaillant',
            'grocery': 'épicerie',
            'food service': 'service alimentaire',
            'restaurant': 'restaurant',
            'sustainability': 'durabilité',
            'sustainable': 'durable',
            'local sourcing': 'approvisionnement local',
            'inventory': 'inventaire',
            'logistics': 'logistique',
            'procurement': 'approvisionnement',
            'supplier': 'fournisseur',
            'vendor': 'vendeur',
            'produce': 'produits frais',
            'dairy': 'produits laitiers',
            'meat': 'viande',
            'poultry': 'volaille',
            'seafood': 'fruits de mer',
            'frozen foods': 'aliments surgelés',
            'fresh foods': 'aliments frais',
            'organic': 'biologique',
            'food safety': 'salubrité alimentaire',
            'traceability': 'traçabilité',
            'cold chain': 'chaîne du froid',
            'delivery': 'livraison',
            'distribution center': 'centre de distribution',
            'warehouse': 'entrepôt',
            'food trends': 'tendances alimentaires',
            'consumer': 'consommateur',
            'demand': 'demande',
            'supply': 'offre',
            'price': 'prix',
            'market': 'marché',
            'inflation': 'inflation',
            'shortage': 'pénurie',
            'surplus': 'surplus'
        }
    
    def _cleanup_expired_cache(self):
        """Nettoyer les fichiers de cache expirés au démarrage"""
        try:
            ttl_seconds = 30 * 24 * 60 * 60  # 30 jours
            current_time = time.time()
            expired_count = 0
            
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.txt'):
                    filepath = os.path.join(self.cache_dir, filename)
                    if os.path.isfile(filepath):
                        file_age = current_time - os.path.getmtime(filepath)
                        if file_age > ttl_seconds:
                            try:
                                os.remove(filepath)
                                expired_count += 1
                            except OSError:
                                pass
            
            if expired_count > 0:
                logger.info(f"Cache nettoyé: {expired_count} fichiers expirés supprimés")
                
        except Exception as e:
            logger.warning(f"Erreur lors du nettoyage du cache: {e}")
    
    def _check_version_compatibility(self):
        """Vérifier la compatibilité de version et invalider cache si nécessaire"""
        version_file = os.path.join(self.cache_dir, 'version.txt')
        
        try:
            # Lire version actuelle du cache
            if os.path.exists(version_file):
                with open(version_file, 'r') as f:
                    cached_version = f.read().strip()
                
                if cached_version != self.TRANSLATOR_VERSION:
                    logger.info(f"Version traducteur changée ({cached_version} → {self.TRANSLATOR_VERSION})")
                    self._invalidate_all_cache()
                    # Écrire nouvelle version
                    with open(version_file, 'w') as f:
                        f.write(self.TRANSLATOR_VERSION)
                else:
                    logger.debug(f"Version traducteur cohérente: {self.TRANSLATOR_VERSION}")
            else:
                # Première installation - créer fichier version
                with open(version_file, 'w') as f:
                    f.write(self.TRANSLATOR_VERSION)
                logger.info(f"Cache traducteur initialisé - version {self.TRANSLATOR_VERSION}")
                
        except Exception as e:
            logger.warning(f"Erreur vérification version traducteur: {e}")
    
    def _invalidate_all_cache(self):
        """Invalider tout le cache de traduction"""
        try:
            invalidated_count = 0
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.txt') and filename != 'version.txt':
                    filepath = os.path.join(self.cache_dir, filename)
                    try:
                        os.remove(filepath)
                        invalidated_count += 1
                    except OSError:
                        pass
            
            logger.info(f"Cache invalidé: {invalidated_count} traductions supprimées")
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'invalidation du cache: {e}")
    
    def _get_cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()
    
    def _load_from_cache(self, cache_key: str) -> Optional[str]:
        """Charger depuis le cache avec validation TTL"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.txt")
        
        if not os.path.exists(cache_file):
            return None
        
        # Vérifier l'âge du fichier (TTL de 30 jours)
        file_age = time.time() - os.path.getmtime(cache_file)
        ttl_seconds = 30 * 24 * 60 * 60  # 30 jours
        
        if file_age > ttl_seconds:
            # Fichier expiré, le supprimer
            try:
                os.remove(cache_file)
                logger.debug(f"Cache expiré supprimé: {cache_key}")
            except OSError:
                pass
            return None
        
        # Charger le contenu valide
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:  # Vérifier que le contenu n'est pas vide
                    return content
        except (IOError, UnicodeDecodeError) as e:
            logger.warning(f"Erreur lecture cache {cache_key}: {e}")
            # Supprimer le fichier corrompu
            try:
                os.remove(cache_file)
            except OSError:
                pass
        
        return None
    
    def _save_to_cache(self, cache_key: str, translation: str):
        """Sauvegarder en cache avec validation"""
        if not translation or not translation.strip():
            logger.warning("Tentative de sauvegarde d'une traduction vide en cache")
            return
        
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.txt")
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(translation.strip())
            logger.debug(f"Traduction mise en cache: {cache_key}")
        except (IOError, OSError) as e:
            logger.warning(f"Impossible de sauvegarder en cache {cache_key}: {e}")
    
    def translate_text(self, text: str, source_lang: str = 'en') -> str:
        if source_lang == 'fr' or not text or len(text.strip()) == 0:
            return text
            
        cache_key = self._get_cache_key(text)
        cached = self._load_from_cache(cache_key)
        if cached:
            return cached
            
        # Essayer DeepL en premier
        if self.translator:
            try:
                # DeepL supporte jusqu'à 130,000 caractères par requête
                result = self.translator.translate_text(
                    text,
                    source_lang="EN",
                    target_lang="FR",  # DeepL utilise "FR" pour le français
                    formality="prefer_more"  # Préférer le vouvoiement
                )
                translated = result.text
                
                # Post-traitement pour améliorer le français québécois et éliminer le tutoiement
                translated = self._quebecois_adjustments(translated)
                translated = self._remove_informal_language(translated)
                self._save_to_cache(cache_key, translated)
                return translated
            except Exception as e:
                logger.warning(f"Erreur DeepL: {e} - utilisation de la traduction de base")
        
        # Sinon utiliser la traduction de base
        translated = self._basic_translate(text)
        self._save_to_cache(cache_key, translated)
        return translated
    
    def _quebecois_adjustments(self, text: str) -> str:
        """Ajustements pour adapter au vocabulaire québécois professionnel"""
        replacements = {
            'e-mail': 'courriel',
            'email': 'courriel',
            'week-end': 'fin de semaine',
            'shopping': 'magasinage',
            'parking': 'stationnement',
            'actualités': 'nouvelles',
            'petit-déjeuner': 'déjeuner',
            'déjeuner': 'dîner',
            'dîner': 'souper',
        }
        
        for fr_term, qc_term in replacements.items():
            text = text.replace(fr_term, qc_term)
            text = text.replace(fr_term.capitalize(), qc_term.capitalize())
            
        return text
    
    def _remove_informal_language(self, text: str) -> str:
        """Éliminer le tutoiement et les formulations informelles"""
        replacements = {
            # Tutoiement -> Vouvoiement
            ' tu ': ' vous ',
            ' tu.': ' vous.',
            ' tu,': ' vous,',
            'Tu ': 'Vous ',
            ' ton ': ' votre ',
            ' ta ': ' votre ',
            ' tes ': ' vos ',
            'Ton ': 'Votre ',
            'Ta ': 'Votre ',
            'Tes ': 'Vos ',
            ' dois ': ' devez ',
            ' peux ': ' pouvez ',
            ' veux ': ' voulez ',
            ' sais ': ' savez ',
            ' es ': ' êtes ',
            ' as ': ' avez ',
            'dois-tu': 'devez-vous',
            'peux-tu': 'pouvez-vous',
            'veux-tu': 'voulez-vous',
        }
        
        for informal, formal in replacements.items():
            text = text.replace(informal, formal)
            
        return text
    
    def _basic_translate(self, text: str) -> str:
        text_lower = text.lower()
        
        for eng_term, fr_term in self.food_terms.items():
            if eng_term in text_lower:
                text = text.replace(eng_term, fr_term)
                text = text.replace(eng_term.capitalize(), fr_term.capitalize())
                text = text.replace(eng_term.upper(), fr_term.upper())
        
        return text
    
    def get_cache_stats(self) -> dict:
        """Obtenir des statistiques sur le cache de traduction"""
        try:
            cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.txt')]
            total_files = len(cache_files)
            
            if total_files == 0:
                return {'total_files': 0, 'total_size_mb': 0, 'oldest_file': None}
            
            total_size = sum(
                os.path.getsize(os.path.join(self.cache_dir, f)) 
                for f in cache_files
            )
            
            oldest_timestamp = min(
                os.path.getmtime(os.path.join(self.cache_dir, f)) 
                for f in cache_files
            )
            
            return {
                'total_files': total_files,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'oldest_file': datetime.fromtimestamp(oldest_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            logger.warning(f"Erreur calcul statistiques cache: {e}")
            return {'error': str(e)}
    
    def translate_if_needed(self, text: str, source: str) -> str:
        english_sources = [
            'Food in Canada', 
            'Canadian Grocer', 
            'Grocery Business', 
            'Western Grocer',
            'The Western Producer',
            'Real Agriculture',
            'Foodservice and Hospitality',
            'Global News',
            'CTV News',
            'CBC News',
            'The Globe and Mail',
            'National Post'
        ]
        
        # Debug logging
        if source in english_sources:
            logger.debug(f"Source anglophone détectée: {source}")
            return self.translate_text(text, 'en')
        else:
            logger.debug(f"Source francophone: {source}")
        
        return text