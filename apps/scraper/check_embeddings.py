import json

with open(r'C:\dev\research\project-iris\apps\scraper\output\faculty_with_embeddings.json', 'r') as f:
    data = json.load(f)

total = len(data)
with_embed = sum(1 for f in data if f.get('embedding'))
sample_len = len(data[0].get('embedding', [])) if data and data[0].get('embedding') else 0

print(f'Total faculty: {total}')
print(f'With embeddings: {with_embed}')
print(f'Embedding dimensions: {sample_len}')
