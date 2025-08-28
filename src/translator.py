import logging
from typing import Optional
import hashlib
import os
from dotenv import load_dotenv

try:
    import deepl
    DEEPL_AVAILABLE = True
except ImportError:
    DEEPL_AVAILABLE = False

logger = logging.getLogger(__name__)

class NewsTranslator:
    def __init__(self):
        self.cache_dir = os.path.join(os.path.dirname(__file__), '..', '.translation_cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
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
    
    def _get_cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()
    
    def _load_from_cache(self, cache_key: str) -> Optional[str]:
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.txt")
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def _save_to_cache(self, cache_key: str, translation: str):
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.txt")
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(translation)
    
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