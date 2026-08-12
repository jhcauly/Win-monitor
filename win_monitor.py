"""Compatibilidade com o prototipo original.

Use `python win_monitor.py` para iniciar o monitor em modo texto.
Para a interface grafica, use `python -m win_monitor.launcher`.
"""

from win_monitor.cli import main


if __name__ == "__main__":
    main()
