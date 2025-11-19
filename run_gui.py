#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Пример использования GUI для алгоритма Хаффмана
"""

import tkinter as tk
from huffman_gui import HuffmanGUI

def main():
    """
    Запуск графического интерфейса
    """
    print("=" * 60)
    print("Графический интерфейс для алгоритма Хаффмана")
    print("=" * 60)
    print()
    print("Возможности:")
    print("  • Интерактивная визуализация дерева")
    print("  • Таблица кодов с частотами")
    print("  • Статистика сжатия")
    print("  • Сжатие/распаковка файлов")
    print()
    print("Управление:")
    print("  • Колесо мыши - масштабирование дерева")
    print("  • ЛКМ + перемещение - перетаскивание дерева")
    print()
    print("Запуск...")
    print()
    
    # Создаем главное окно
    root = tk.Tk()
    
    # Запускаем приложение
    app = HuffmanGUI(root)
    
    # Главный цикл
    root.mainloop()
    
    print()
    print("Программа завершена.")


if __name__ == "__main__":
    main()