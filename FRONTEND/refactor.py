import os, re
src_dir='src/actions'
files=os.listdir(src_dir)
for f in files:
    if f.endswith('.ts'):
        p = os.path.join(src_dir, f)
        with open(p, 'r') as file: content = file.read()
        
        # Remove import Database
        content = re.sub(r"import Database from ['\"]better-sqlite3['\"];?\n?", "", content)
        # Remove import path
        content = re.sub(r"import path from ['\"]path['\"];?\n?", "", content)
        # Remove const dbPath = ...
        content = re.sub(r"const dbPath = path\.resolve.*?;\n?", "", content)
        # Remove local getDb() definition
        content = re.sub(r"const getDb = \(\) => \{\s*const dbPath = path\.resolve.*?;\s*return new Database\(dbPath\);\s*\};\n?", "", content)
        # Handle specific dbPath variations
        content = re.sub(r"const dbPath =.*?;\n?", "", content)
        content = re.sub(r"const db = new Database\(['\"].*?vigbot.db['\"]\);", "const db = getDb();", content)
        
        # Replace new Database(dbPath) with getDb()
        content = content.replace("new Database(dbPath)", "getDb()")
        
        # Add import { getDb }
        if "getDb" in content and "import { getDb }" not in content:
            if "\"use server\";" in content:
                content = content.replace("\"use server\";", "\"use server\";\n\nimport { getDb } from \"../lib/db-provider\";")
            elif "'use server';" in content:
                content = content.replace("'use server';", "'use server';\n\nimport { getDb } from \"../lib/db-provider\";")
            else:
                content = "import { getDb } from \"../lib/db-provider\";\n" + content
                
        with open(p, 'w') as file: file.write(content)
