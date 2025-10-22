import os
import json
import requests
from datetime import datetime
import re
from urllib.parse import quote_plus

# Configurazione
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

SEARCH_QUERIES = [
    "EDM machine news 2025",
    "wire EDM innovation",
    "electrical discharge machining technology",
    "Sodick EDM new model",
    "GF Machining Solutions EDM",
    "Mitsubishi EDM updates",
    "EDM manufacturing breakthrough"
]

CATEGORIES = [
    "Nuovi Modelli",
    "Innovazioni Tecnologiche", 
    "Aziende e Mercato",
    "Ricerca e Brevetti",
    "Eventi e Fiere"
]

def search_google_news(query):
    """Cerca notizie usando Google News RSS"""
    try:
        url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', response.text)
            descriptions = re.findall(r'<description><!\[CDATA\[(.*?)\]\]></description>', response.text)
            links = re.findall(r'<link>(.*?)</link>', response.text)
            
            results = []
            for i in range(1, min(len(titles), 6)):  # Skip first (feed title), max 5
                title = titles[i] if i < len(titles) else ""
                desc = descriptions[i-1] if i-1 < len(descriptions) else title
                link = links[i] if i < len(links) else ""
                
                # Pulisci HTML dal description
                desc_clean = re.sub(r'<.*?>', '', desc)
                
                results.append({
                    'title': title,
                    'snippet': desc_clean[:300],
                    'url': link,
                    'source': 'Google News'
                })
            
            return results
        
    except Exception as e:
        print(f"   Errore ricerca: {e}")
    
    return []

def analyze_with_gemini(all_results):
    """Usa Gemini per analizzare i risultati"""
    
    if not GOOGLE_API_KEY:
        print("❌ GOOGLE_API_KEY non configurata!")
        return {"notizie": []}
    
    # Prepara il contenuto per Gemini
    content_summary = []
    for result in all_results[:20]:  # Max 20 articoli per non superare i limiti
        content_summary.append(f"Titolo: {result.get('title', '')}\nContenuto: {result.get('snippet', '')}\n")
    
    combined_content = "\n---\n".join(content_summary)
    
    prompt = f"""Analizza questi articoli sulle macchine EDM (Electrical Discharge Machining / elettroerosione).

ARTICOLI:
{combined_content}

COMPITO:
1. Identifica SOLO le notizie veramente rilevanti sulle macchine EDM
2. Ignora articoli generici o non pertinenti
3. Per ogni notizia rilevante, categorizzala in una di queste categorie:
   - Nuovi Modelli
   - Innovazioni Tecnologiche
   - Aziende e Mercato
   - Ricerca e Brevetti
   - Eventi e Fiere

4. Crea un riassunto chiaro in italiano (2-3 frasi)
5. Assegna un punteggio di importanza da 1 a 10

FORMATO DI RISPOSTA (SOLO JSON, nessun altro testo):
{{
  "notizie": [
    {{
      "titolo": "titolo in italiano",
      "categoria": "una delle 5 categorie",
      "riassunto": "riassunto in italiano di 2-3 frasi",
      "importanza": 7,
      "fonte": "nome fonte",
      "data": "2025-10-22"
    }}
  ]
}}

Rispondi SOLO con JSON valido, senza markdown o altri testi."""

    try:
        # Chiamata API Gemini
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GOOGLE_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 2048
            }
        }
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Estrai il testo dalla risposta
            if 'candidates' in data and len(data['candidates']) > 0:
                text = data['candidates'][0]['content']['parts'][0]['text']
                
                # Pulisci il testo da eventuali markdown
                text = text.strip()
                text = re.sub(r'```json\s*', '', text)
                text = re.sub(r'```\s*', '', text)
                text = text.strip()
                
                # Parse JSON
                result = json.loads(text)
                return result
            else:
                print("⚠️ Risposta API vuota")
                return {"notizie": []}
        else:
            print(f"❌ Errore API Gemini: {response.status_code}")
            print(f"Risposta: {response.text[:200]}")
            return {"notizie": []}
            
    except json.JSONDecodeError as e:
        print(f"❌ Errore parsing JSON: {e}")
        print(f"Testo ricevuto: {text[:200] if 'text' in locals() else 'N/A'}")
        return {"notizie": []}
    except Exception as e:
        print(f"❌ Errore Gemini: {e}")
        return {"notizie": []}

def save_results(notizie, filename='data/edm_news.json'):
    """Salva i risultati"""
    os.makedirs('data', exist_ok=True)
    
    existing_data = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except:
            existing_data = []
    
    new_entry = {
        'timestamp': datetime.now().isoformat(),
        'data': {'notizie': notizie}
    }
    existing_data.append(new_entry)
    existing_data = existing_data[-100:]
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Risultati salvati in {filename}")

def main():
    print("🤖 Avvio Agente AI Monitoraggio EDM con Gemini...")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    if not GOOGLE_API_KEY:
        print("❌ ERRORE: GOOGLE_API_KEY non configurata!")
        print("Aggiungi la chiave nei GitHub Secrets")
        return
    
    # Raccogli notizie
    all_results = []
    print("🔍 Ricerca notizie...")
    for query in SEARCH_QUERIES:
        print(f"   • {query}")
        results = search_google_news(query)
        if results:
            all_results.extend(results)
            print(f"     ✓ {len(results)} risultati")
        else:
            print(f"     ⚠ Nessun risultato")
    
    print(f"\n📊 Totale articoli raccolti: {len(all_results)}")
    
    if len(all_results) == 0:
        print("⚠️ Nessun articolo trovato nelle ricerche")
        save_results([])
        return
    
    # Analizza con Gemini
    print("\n🧠 Analisi con Gemini AI...")
    analyzed = analyze_with_gemini(all_results)
    
    notizie = analyzed.get('notizie', [])
    
    if notizie:
        # Ordina per importanza
        notizie.sort(key=lambda x: x.get('importanza', 0), reverse=True)
        
        save_results(notizie)
        print(f"\n✨ Salvate {len(notizie)} notizie rilevanti!")
        
        print("\n📰 Top 5 notizie:")
        for i, news in enumerate(notizie[:5], 1):
            print(f"{i}. [{news.get('importanza', 0)}/10] {news.get('titolo', 'N/A')[:70]}...")
    else:
        print("\n⚠️ Gemini non ha trovato notizie rilevanti")
        save_results([])
    
    print("\n✅ Agente completato!")

if __name__ == "__main__":
    main()
