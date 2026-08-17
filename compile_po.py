# compile_po.py
import polib
from pathlib import Path

def ensure_locale_structure():
    """Crée les dossiers et fichiers .po s'ils n'existent pas."""
    locale_dir = Path("locale")
    languages = ["fr", "en"]

    for lang in languages:
        po_dir = locale_dir / lang / "LC_MESSAGES"
        po_dir.mkdir(parents=True, exist_ok=True)
        po_file = po_dir / "messages.po"

        if not po_file.exists():
            # Créer un fichier .po minimal avec en-tête
            po_content = f'''msgid ""
msgstr ""
"Project-Id-Version: PythonCodeExtractor 1.0\\n"
"POT-Creation-Date: 2026-08-13 11:00+0200\\n"
"PO-Revision-Date: 2026-08-13 11:00+0200\\n"
"Last-Translator: \\n"
"Language-Team: \\n"
"Language: {lang}\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
'''
            with open(po_file, 'w', encoding='utf-8') as f:
                f.write(po_content)
            print(f"✅ Fichier {po_file} créé.")

def compile_all_po():
    """Compile tous les fichiers .po en .mo."""
    locale_dir = Path("locale")
    if not locale_dir.exists():
        print("❌ Le dossier 'locale' n'existe pas. Création...")
        ensure_locale_structure()

    for lang_dir in locale_dir.iterdir():
        if lang_dir.is_dir():
            po_file = lang_dir / "LC_MESSAGES" / "messages.po"
            mo_file = lang_dir / "LC_MESSAGES" / "messages.mo"
            if po_file.exists():
                try:
                    po = polib.pofile(str(po_file))
                    po.save_as_mofile(str(mo_file))
                    print(f"✅ {mo_file} généré avec succès")
                except Exception as e:
                    print(f"❌ Erreur pour {po_file} : {e}")
            else:
                print(f"⚠️  {po_file} manquant, ignoré.")

if __name__ == "__main__":
    ensure_locale_structure()
    compile_all_po()
    print("✅ Compilation terminée.")