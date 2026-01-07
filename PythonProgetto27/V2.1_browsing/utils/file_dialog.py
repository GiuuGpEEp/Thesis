import os

def choose_xml_file(initial_dir=None, title="Seleziona il file ITINERARI.xml:"):
    """
    Restituisce il percorso selezionato o None se annullato.
    Usa tkinter se disponibile, altrimenti fallback su input().
    """
    initial_dir = initial_dir or os.getcwd()
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            title=title,
            initialdir=initial_dir,
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        root.destroy()
        if path:
            return path
    except Exception:
        # ambiente headless o tkinter non installato -> fallback testuale
        pass

    # fallback testuale
    p = input(f"Inserisci percorso file XML (default: {initial_dir}): ").strip()
    return p if p else None

def choose_output_directory(initial_dir=None, title="Seleziona directory di output"):
    """
    Restituisce il percorso della directory selezionata o None se annullato.
    Usa tkinter se disponibile, altrimenti fallback su input().
    """
    initial_dir = initial_dir or os.getcwd()
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askdirectory(
            title=title,
            initialdir=initial_dir
        )
        root.destroy()
        if path:
            return path
    except Exception:
        # ambiente headless o tkinter non installato -> fallback testuale
        pass

    # fallback testuale
    p = input(f"Inserisci percorso directory di output (default: {initial_dir}): ").strip()
    return p if p else None