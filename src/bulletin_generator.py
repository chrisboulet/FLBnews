from jinja2 import Template
from datetime import datetime
from typing import List
import os
import locale
from scraper import NewsItem

try:
    locale.setlocale(locale.LC_TIME, 'fr_CA.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    except:
        pass

MOIS_FR = {
    1: 'janvier', 2: 'février', 3: 'mars', 4: 'avril',
    5: 'mai', 6: 'juin', 7: 'juillet', 8: 'août',
    9: 'septembre', 10: 'octobre', 11: 'novembre', 12: 'décembre'
}

class BulletinGenerator:
    def __init__(self, template_path: str = None):
        self.template = self._load_template(template_path)
    
    def format_date_fr(self, date: datetime) -> str:
        return f"{date.day} {MOIS_FR[date.month]} {date.year}"
        
    def _load_template(self, template_path: str = None) -> Template:
        if template_path and os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                template_str = f.read()
        else:
            template_str = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bulletin de Nouvelles FLB - {{ date }}</title>
    <link href="https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700;900&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Lato', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #2c2c2c;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #009A48 0%, #007835 100%);
            color: white;
            padding: 40px 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0, 154, 72, 0.15);
            position: relative;
            overflow: hidden;
        }
        .header::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -10%;
            width: 40%;
            height: 200%;
            background: rgba(255, 148, 22, 0.1);
            transform: rotate(45deg);
        }
        .logo {
            display: inline-block;
            margin-bottom: 20px;
        }
        .header h1 {
            font-size: 2.8em;
            font-weight: 900;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
            letter-spacing: -1px;
        }
        .subtitle {
            font-size: 1.2em;
            font-weight: 300;
            opacity: 0.95;
            margin-bottom: 15px;
        }
        .date {
            display: inline-block;
            background: rgba(255, 255, 255, 0.2);
            padding: 8px 20px;
            border-radius: 25px;
            font-weight: 400;
            margin-top: 10px;
        }
        .summary-box {
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 40px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.08);
            border-left: 5px solid #FF9416;
        }
        .summary-box h2 {
            color: #009A48;
            font-size: 1.8em;
            font-weight: 700;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .summary-box h2::before {
            content: '📊';
            font-size: 1.2em;
        }
        .summary-box p {
            color: #555;
            line-height: 1.8;
            font-size: 1.05em;
        }
        .news-container {
            display: grid;
            gap: 30px;
        }
        .news-item {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 20px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
            position: relative;
        }
        .news-item::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #009A48 0%, #FF9416 100%);
        }
        .news-item:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 40px rgba(0, 154, 72, 0.15);
        }
        .news-content {
            padding: 25px;
        }
        .news-title {
            color: #2c2c2c;
            font-size: 1.5em;
            margin-bottom: 15px;
            font-weight: 700;
            line-height: 1.3;
        }
        .news-title a {
            color: inherit;
            text-decoration: none;
            transition: color 0.3s ease;
        }
        .news-title a:hover {
            color: #009A48;
        }
        .news-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid #f0f0f0;
            flex-wrap: wrap;
            gap: 10px;
        }
        .source {
            background: linear-gradient(135deg, #009A48 0%, #007835 100%);
            color: white;
            padding: 6px 16px;
            border-radius: 25px;
            font-size: 0.85em;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .date-published {
            color: #888;
            font-size: 0.9em;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .date-published::before {
            content: '📅';
        }
        .summary {
            color: #444;
            margin: 20px 0;
            line-height: 1.8;
            font-size: 1.02em;
            text-align: justify;
        }
        .summary p {
            margin-bottom: 12px;
        }
        .summary p:last-child {
            margin-bottom: 0;
        }
        .read-more {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #FF9416;
            font-weight: 700;
            text-decoration: none;
            margin-top: 15px;
            transition: all 0.3s ease;
        }
        .read-more:hover {
            color: #e57f00;
            gap: 12px;
        }
        .read-more::after {
            content: '→';
            font-size: 1.2em;
        }
        .relevance {
            background: linear-gradient(135deg, #fff8f0 0%, #ffeedb 100%);
            border-left: 4px solid #FF9416;
            padding: 15px 20px;
            margin: 20px 0;
            border-radius: 8px;
            font-size: 0.95em;
            position: relative;
        }
        .relevance::before {
            content: '💡';
            position: absolute;
            left: -15px;
            top: 50%;
            transform: translateY(-50%);
            background: white;
            padding: 5px;
            border-radius: 50%;
        }
        .relevance strong {
            color: #d47300;
            font-weight: 700;
        }
        .tags {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #f0f0f0;
        }
        .tag {
            background: #f8f9fa;
            color: #666;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            transition: all 0.3s ease;
            border: 1px solid #e9ecef;
        }
        .tag:hover {
            background: #009A48;
            color: white;
            border-color: #009A48;
        }
        .footer {
            text-align: center;
            margin-top: 60px;
            padding: 40px 30px;
            background: linear-gradient(135deg, #2c2c2c 0%, #1a1a1a 100%);
            border-radius: 15px;
            color: white;
            position: relative;
            overflow: hidden;
        }
        .footer::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #009A48 0%, #FF9416 50%, #009A48 100%);
        }
        .footer-logo {
            font-size: 1.5em;
            font-weight: 900;
            color: #009A48;
            margin-bottom: 15px;
        }
        .company-info {
            margin: 15px 0;
            font-size: 1em;
            opacity: 0.9;
        }
        .company-info a {
            color: #FF9416;
            text-decoration: none;
            font-weight: 700;
        }
        .company-info a:hover {
            text-decoration: underline;
        }
        .no-news {
            text-align: center;
            padding: 40px;
            background: white;
            border-radius: 10px;
            color: #666;
        }
        @media (max-width: 600px) {
            body {
                padding: 10px;
            }
            .header h1 {
                font-size: 1.8em;
            }
            .news-meta {
                flex-direction: column;
                align-items: flex-start;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🍎</div>
            <h1>Bulletin FLB Solutions</h1>
            <div class="subtitle">Votre veille stratégique de l'industrie alimentaire</div>
            <div class="date">{{ date }}</div>
        </div>
        
        <div class="summary-box">
            <h2>Sommaire de la semaine</h2>
            <p>Nous avons sélectionné <strong style="color: #FF9416;">{{ news_count }}</strong> articles essentiels pour FLB Solutions alimentaires. Cette sélection couvre les <strong>tendances du marché</strong>, les <strong>innovations en distribution</strong>, et les <strong>développements régionaux</strong> qui impactent directement votre secteur d'activité.</p>
        </div>
    
    {% if news_items %}
    <div class="news-container">
        {% for item in news_items %}
        <div class="news-item">
            <div class="news-content">
                <h3 class="news-title">
                    <a href="{{ item.url }}" target="_blank">{{ item.title }}</a>
                </h3>
                
                <div class="news-meta">
                    <span class="source">{{ item.source }}</span>
                    {% if item.published_date %}
                    <span class="date-published">{{ format_date_fr(item.published_date) if item.published_date else '' }}</span>
                    {% endif %}
                </div>
                
                <div class="summary">
                    {{ item.summary[:1800] }}{% if item.summary|length > 1800 %}...{% endif %}
                </div>
                
                <a href="{{ item.url }}" target="_blank" class="read-more">Lire l'article complet</a>
            
            {% if item.relevance_to_flb %}
            <div class="relevance">
                <strong>Pertinence pour FLB:</strong> {{ item.relevance_to_flb }}
            </div>
            {% endif %}
            
            {% if item.tags %}
            <div class="tags">
                {% for tag in item.tags[:5] %}
                <span class="tag">{{ tag }}</span>
                {% endfor %}
            </div>
            {% endif %}
            </div>
        </div>
        {% endfor %}
    </div>
    {% else %}
    <div class="no-news">
        <p>Aucune nouvelle pertinente trouvée pour cette période.</p>
    </div>
    {% endif %}
    
        <div class="footer">
            <div class="footer-logo">FLB SOLUTIONS ALIMENTAIRES</div>
            <div class="company-info">
                📍 275 avenue du Semoir, Québec<br>
                🌐 <a href="https://flbsolutions.com" target="_blank">www.flbsolutions.com</a>
            </div>
            <div style="margin-top: 20px; font-size: 0.85em; opacity: 0.7;">
                Bulletin généré automatiquement le {{ generation_time }}<br>
                © {{ current_year }} FLB Solutions alimentaires - Tous droits réservés
            </div>
        </div>
    </div>
</body>
</html>
'''
        return Template(template_str)
    
    def generate_bulletin(self, news_items: List[NewsItem], output_path: str = None) -> str:
        bulletin_html = self.template.render(
            news_items=news_items,
            news_count=len(news_items),
            date=self.format_date_fr(datetime.now()),
            generation_time=datetime.now().strftime('%d/%m/%Y à %H:%M'),
            current_year=datetime.now().year,
            format_date_fr=self.format_date_fr
        )
        
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(bulletin_html)
                
        return bulletin_html
    
    def generate_email_version(self, news_items: List[NewsItem]) -> str:
        email_template = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { background-color: #003d7a; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .news-item { margin-bottom: 20px; padding: 15px; background: #f9f9f9; border-left: 3px solid #0056b3; }
        .news-title { color: #003d7a; margin: 0 0 10px; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Bulletin de Nouvelles FLB</h1>
        <p>{{ date }}</p>
    </div>
    
    <div class="content">
        <p>Bonjour,</p>
        <p>Veuillez trouver ci-dessous les {{ news_count }} nouvelles pertinentes de l'industrie alimentaire pour cette semaine :</p>
        
        {% for item in news_items[:5] %}
        <div class="news-item">
            <h3 class="news-title">{{ item.title }}</h3>
            <p><strong>Source:</strong> {{ item.source }}</p>
            <p>{{ item.summary[:1800] }}{% if item.summary|length > 1800 %}...{% endif %}</p>
            <p><a href="{{ item.url }}">Lire l'article complet →</a></p>
        </div>
        {% endfor %}
        
        {% if news_items|length > 5 %}
        <p><em>... et {{ news_items|length - 5 }} autres nouvelles disponibles dans le bulletin complet.</em></p>
        {% endif %}
    </div>
    
    <div class="footer">
        <p>FLB Solutions alimentaires<br>
        275 avenue du Semoir, Québec<br>
        <a href="https://flbsolutions.com">flbsolutions.com</a></p>
    </div>
</body>
</html>
'''
        
        template = Template(email_template)
        return template.render(
            news_items=news_items,
            news_count=len(news_items),
            date=self.format_date_fr(datetime.now())
        )