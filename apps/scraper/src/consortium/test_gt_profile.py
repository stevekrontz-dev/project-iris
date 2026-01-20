import asyncio
import aiohttp
import json
import re

THALAMUS_URL = 'http://localhost:3000'

async def scrape_gt_bme_full():
    async with aiohttp.ClientSession() as session:
        # Step 1: Get names from index page
        print('Phase 1: Getting faculty list from index...')
        perceive = {
            'method': 'tools/call',
            'params': {
                'name': 'thalamus_perceive',
                'arguments': {
                    'url': 'https://bme.gatech.edu/our-people/our-faculty',
                    'maxElements': 200
                }
            },
            'id': 'gt-index'
        }
        async with session.post(THALAMUS_URL + '/mcp', json=perceive, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            await resp.json()
        
        await asyncio.sleep(2)
        
        get_text = {
            'method': 'tools/call',
            'params': {'name': 'thalamus_get_text', 'arguments': {'maxLength': 50000}},
            'id': 'gt-text'
        }
        async with session.post(THALAMUS_URL + '/mcp', json=get_text, timeout=aiohttp.ClientTimeout(total=20)) as resp:
            result = await resp.json()
            content = result['result']['content'][0]['text']
            text_data = json.loads(content)
        
        # Extract names
        title_words = ['professor', 'director', 'chair', 'fellow', 'associate', 'senior', 
                       'lecturer', 'scholar', 'emeritus', 'professorship', 'distinguished',
                       'academic', 'professional', 'coordinator', 'specialist', 'services',
                       'faculty', 'biomedical', 'engineering', 'results', 'page']
        
        names = []
        for block in text_data.get('content', []):
            text = block.get('text', '').strip()
            if not text or len(text) < 5 or len(text) > 50:
                continue
            text_lower = text.lower()
            if any(tw in text_lower for tw in title_words):
                continue
            if ' ' not in text:
                continue
            words = text.replace('(', ' ').replace(')', ' ').split()
            if len(words) < 2 or len(words) > 5:
                continue
            cap_words = sum(1 for w in words if w and w[0].isupper())
            if cap_words >= len(words) * 0.5:
                names.append(text)
        
        print(f'Found {len(names)} names on page 1')
        for n in names[:5]:
            print(f'  - {n}')
        
        # Step 2: Visit first profile to test
        if names:
            name = names[0]
            # Convert name to URL slug
            slug = re.sub(r'[^a-zA-Z0-9\s]', '', name).lower().replace(' ', '-')
            profile_url = f'https://bme.gatech.edu/bio/{slug}'
            
            print(f'\nPhase 2: Testing profile page for {name}')
            print(f'  URL: {profile_url}')
            
            perceive2 = {
                'method': 'tools/call',
                'params': {
                    'name': 'thalamus_perceive',
                    'arguments': {'url': profile_url, 'maxElements': 100}
                },
                'id': 'gt-profile'
            }
            async with session.post(THALAMUS_URL + '/mcp', json=perceive2, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                result = await resp.json()
                if result.get('error'):
                    print(f'  Error: {result.get("error")}')
                    return
            
            await asyncio.sleep(2)
            
            get_text2 = {
                'method': 'tools/call',
                'params': {'name': 'thalamus_get_text', 'arguments': {'maxLength': 20000}},
                'id': 'gt-profile-text'
            }
            async with session.post(THALAMUS_URL + '/mcp', json=get_text2, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                result = await resp.json()
                content = result['result']['content'][0]['text']
                profile_data = json.loads(content)
            
            print(f'\n  Profile content for {name}:')
            print(f'  =' * 40)
            for block in profile_data.get('content', [])[:20]:
                text = block.get('text', '')
                if len(text) > 100:
                    text = text[:100] + '...'
                print(f'    {block["type"]}: {text}')

if __name__ == '__main__':
    asyncio.run(scrape_gt_bme_full())
