import os

def replace_img_with_next_image(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if "import Image from" not in content and "next/image" not in content:
        # insert after first import
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith("import"):
                lines.insert(i + 1, 'import Image from "next/image";')
                break
        content = '\n'.join(lines)
    
    # Simple replacements for the specific known cases
    # Sidebar.tsx
    content = content.replace(
        '<img\n                  src="/vignan-logo.png"\n                  alt="Vignan\'s University"\n                  className="h-12 w-auto max-w-[155px] object-contain drop-shadow-xs group-hover:scale-[1.02] transition-transform shrink-0"\n                />',
        '<Image\n                  src="/vignan-logo.png"\n                  alt="Vignan\'s University"\n                  width={155}\n                  height={48}\n                  className="h-12 w-auto max-w-[155px] object-contain drop-shadow-xs group-hover:scale-[1.02] transition-transform shrink-0"\n                />'
    )
    content = content.replace(
        '<img\n                  src="/vignan-logo.png"\n                  alt="Vignan\'s University"\n                  className="h-8 w-auto object-contain drop-shadow-xs"\n                />',
        '<Image\n                  src="/vignan-logo.png"\n                  alt="Vignan\'s University"\n                  width={100}\n                  height={32}\n                  className="h-8 w-auto object-contain drop-shadow-xs"\n                />'
    )
    
    # LandingPage.tsx
    content = content.replace(
        '<img\n              src="/vignan-logo.png"\n              alt="Vignan Foundation"\n              className="h-9 sm:h-11 w-auto object-contain"\n            />',
        '<Image\n              src="/vignan-logo.png"\n              alt="Vignan Foundation"\n              width={140}\n              height={44}\n              className="h-9 sm:h-11 w-auto object-contain"\n            />'
    )

    # Header.tsx
    content = content.replace(
        '<img\n            src="/vignan-logo.png"\n            alt="Vignan\'s University"\n            className="h-9 w-auto object-contain"\n          />',
        '<Image\n            src="/vignan-logo.png"\n            alt="Vignan\'s University"\n            width={120}\n            height={36}\n            className="h-9 w-auto object-contain"\n          />'
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    files = [
        "C:/StudentHelpdesk/FRONTEND/src/components/sidebar/Sidebar.tsx",
        "C:/StudentHelpdesk/FRONTEND/src/components/landing/LandingPage.tsx",
        "C:/StudentHelpdesk/FRONTEND/src/components/header/Header.tsx"
    ]
    for f in files:
        if os.path.exists(f):
            replace_img_with_next_image(f)
            print(f"Updated {f}")
