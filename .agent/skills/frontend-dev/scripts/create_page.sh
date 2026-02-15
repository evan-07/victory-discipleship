#!/bin/bash
# Scaffolds a new HTML page in frontend/
# Usage: ./create_page.sh <page_name>

if [ -z "$1" ]; then
    echo "Usage: ./create_page.sh <page_name>"
    exit 1
fi
    
page_name=$1
target_file="frontend/${page_name}.html"

if [ -f "$target_file" ]; then
    echo "Error: $target_file already exists."
    exit 1
fi

cat <<EOF > "$target_file"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${page_name}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <h1>${page_name}</h1>
    </header>
    <main>
        <p>Content goes here.</p>
    </main>
    <footer>
        <p>&copy; 2024 Victory Discipleship</p>
    </footer>
    <script src="script.js"></script>
</body>
</html>
EOF

echo "Created $target_file"
