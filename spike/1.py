python3 -c "
import json
tot = tag = 0
for line in open('data/poi_real_chicken.jsonl', encoding='utf-8'):
    p = json.loads(line)
    tot += 1
    t = p.get('tag')
    if isinstance(t, str) and t.strip(): tag += 1
print(f'真实POI {tot} 条 | tag非空 {tag} 条 | 覆盖率 {tag/tot:.1%}')
"