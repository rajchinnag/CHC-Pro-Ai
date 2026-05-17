content = open('src/services/uploadService.js', 'r', encoding='utf-8').read()

# Replace axios calls with api calls (remove headers and use relative paths)
import re

# Remove the API constant line if still there
content = re.sub(r"\nconst API = .*;\n", "\n", content)

# Replace axios.post(..., { headers: authHeader() }) -> api.post(...)
content = re.sub(
    r'axios\.post\(\s*\$\{API\}(/[^]+),\s*(\{[^}]+\}),\s*\{ headers: authHeader\(\) \}\)',
    r'api.post(\1, \2)',
    content
)

# Replace axios.get with headers
content = re.sub(
    r'axios\.get\(\$\{API\}(/[^]+), \{\s*headers: authHeader\(\),\s*params: ([^}]+)\}\)',
    r'api.get(\1, { params: \2})',
    content
)
content = re.sub(
    r'axios\.get\(\$\{API\}(/[^]+), \{\s*headers: authHeader\(\),?\s*\}\)',
    r'api.get(\1)',
    content
)

# Replace axios.delete
content = re.sub(
    r'axios\.delete\(\$\{API\}(/[^]+), \{\s*headers: authHeader\(\),?\s*\}\)',
    r'api.delete(\1)',
    content
)

open('src/services/uploadService.js', 'w', encoding='utf-8').write(content)
print('Done!')
