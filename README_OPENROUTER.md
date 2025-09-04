# Configuration OpenRouter pour FLB News

## Installation réussie!

OpenRouter avec O4 est maintenant intégré à votre application FLB News.

## Configuration

### 1. Clé API
Votre clé API OpenRouter doit être stockée dans le fichier `.env`:
```
OPENROUTER_API_KEY=votre_clé_api_ici
```
⚠️ **SÉCURITÉ**: Ne jamais committer votre clé API dans le repository. Ajoutez toujours le fichier `.env` à votre `.gitignore`.

### 2. Modèle configuré
- **Modèle**: `openai/o4` (migration depuis GPT-5 pour une meilleure stabilité)
- **Mode**: Premium (analyse approfondie)
- **Articles analysés**: Top 7 articles avec article vedette

## Utilisation

### Génération normale de bulletin avec OpenRouter

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Générer un bulletin avec analyse O4
python main.py
```

### Test de l'intégration

```bash
# Test rapide de l'analyse OpenRouter
python test_openrouter.py

# Test complet avec génération de bulletin
python test_integration_openrouter.py
```

## Fonctionnalités activées

### Nouvelles améliorations (28 août 2025):
- **Migration vers O4**: Remplacement de GPT-5 par O4 pour une meilleure stabilité et performance
- **7 articles avec article vedette**: Le bulletin affiche maintenant 7 articles, le dernier étant mis en vedette
- **Support des images**: Extraction automatique et affichage des images pour chaque article
- **Extraction améliorée**: Récupération des images depuis RSS, Open Graph et contenu des articles

### Fonctionnalités de base

1. **Analyse hybride**: 
   - BM25 pour le scoring rapide
   - O4 pour l'analyse approfondie des top articles

2. **Enrichissement intelligent**:
   - Impact business détaillé
   - Insights stratégiques
   - Actions recommandées spécifiques à FLB

3. **Optimisation des coûts**:
   - Les 7 articles les plus pertinents sont analysés avec O4
   - Cache des analyses pour éviter les appels redondants

## Configuration avancée

Pour modifier les paramètres, éditez `config_openrouter.py`:

- `max_openrouter_articles`: Nombre d'articles à analyser avec O4 (défaut: 7)
- `openrouter_model`: Modèle à utiliser (défaut: 'openai/o4')
- `mode`: 'economique', 'standard', ou 'premium'

## Coûts estimés

Avec la configuration actuelle:
- ~7 articles analysés par bulletin (6 normaux + 1 vedette)
- ~800 tokens max par analyse
- Coût approximatif: voir [OpenRouter Pricing](https://openrouter.ai/models)

## Dépannage

Si l'analyse OpenRouter ne fonctionne pas:

1. Vérifiez que la clé API est valide
2. Vérifiez votre connexion internet
3. Consultez les logs pour les messages d'erreur
4. Testez avec: `python test_openrouter.py`

## Support

Pour toute question sur OpenRouter:
- Documentation: https://openrouter.ai/docs
- Modèles disponibles: https://openrouter.ai/models