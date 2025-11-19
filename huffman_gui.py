import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import math

# Импортируем классы из huffman.py
from huffman import HuffmanCoder, compress_file, decompress_file


class TreeVisualizer(tk.Canvas):
    """Интерактивная визуализация дерева Хаффмана"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg='#f0f0f0')
        
        # Параметры визуализации
        self.node_radius = 25
        self.level_height = 100
        self.min_horizontal_spacing = 80  # Минимальное расстояние между узлами по горизонтали
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 50
        
        # Для перетаскивания
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # Данные дерева
        self.tree_root = None
        self.node_positions = {}
        
        # Привязка событий
        self.bind('<MouseWheel>', self.on_mousewheel)
        self.bind('<Button-4>', self.on_mousewheel)  # Linux
        self.bind('<Button-5>', self.on_mousewheel)  # Linux
        self.bind('<ButtonPress-1>', self.on_drag_start)
        self.bind('<B1-Motion>', self.on_drag_motion)
        
    def on_mousewheel(self, event):
        """Масштабирование колесиком мыши"""
        # Получаем позицию мыши
        x = self.canvasx(event.x)
        y = self.canvasy(event.y)
        
        # Определяем направление прокрутки
        if event.num == 5 or event.delta < 0:
            scale = 0.9
        else:
            scale = 1.1
        
        # Ограничиваем масштаб
        new_scale = self.scale_factor * scale
        if 0.3 <= new_scale <= 3.0:
            self.scale_factor = new_scale
            self.draw_tree()
    
    def on_drag_start(self, event):
        """Начало перетаскивания"""
        self.drag_start_x = event.x
        self.drag_start_y = event.y
    
    def on_drag_motion(self, event):
        """Перетаскивание холста"""
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        
        self.offset_x += dx
        self.offset_y += dy
        
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
        self.draw_tree()
    
    def set_tree(self, tree_root):
        """Установка дерева для визуализации"""
        self.tree_root = tree_root
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        # Задержка для корректного получения размеров canvas
        self.after(100, self.draw_tree)
    
    def calculate_tree_width(self, node):
        """Вычисление количества листьев в поддереве"""
        if node is None:
            return 0
        
        if node.left is None and node.right is None:
            return 1
        
        left_width = self.calculate_tree_width(node.left)
        right_width = self.calculate_tree_width(node.right)
        
        return left_width + right_width
    
    def get_tree_bounds(self, node, x, y):
        """Получение границ поддерева (минимальный и максимальный X)"""
        if node is None:
            return x, x
        
        if node.left is None and node.right is None:
            return x, x
        
        min_x = x
        max_x = x
        
        if node.left:
            left_min, left_max = self.get_tree_bounds(node.left, x, y)
            min_x = min(min_x, left_min)
            max_x = max(max_x, left_max)
        
        if node.right:
            right_min, right_max = self.get_tree_bounds(node.right, x, y)
            min_x = min(min_x, right_min)
            max_x = max(max_x, right_max)
        
        return min_x, max_x
    
    def calculate_positions(self, node, x, y, next_leaf_x=[0]):
        """Улучшенное рекурсивное вычисление позиций узлов"""
        if node is None:
            return x, x
        
        if node.left is None and node.right is None:
            # Листовой узел - размещаем на следующей доступной позиции
            leaf_x = next_leaf_x[0]
            next_leaf_x[0] += self.min_horizontal_spacing
            self.node_positions[id(node)] = (leaf_x, y)
            return leaf_x, leaf_x
        
        # Внутренний узел - сначала размещаем детей
        next_y = y + self.level_height
        
        left_min = left_max = x
        right_min = right_max = x
        
        if node.left:
            left_min, left_max = self.calculate_positions(node.left, x, next_y, next_leaf_x)
        
        if node.right:
            right_min, right_max = self.calculate_positions(node.right, x, next_y, next_leaf_x)
        
        # Размещаем текущий узел по центру между крайними потомками
        if node.left and node.right:
            node_x = (left_min + right_max) / 2
        elif node.left:
            node_x = (left_min + left_max) / 2
        elif node.right:
            node_x = (right_min + right_max) / 2
        else:
            node_x = x
        
        self.node_positions[id(node)] = (node_x, y)
        
        # Возвращаем границы поддерева
        min_x = left_min if node.left else node_x
        max_x = right_max if node.right else node_x
        
        return min_x, max_x
    
    def draw_tree(self):
        """Отрисовка дерева"""
        self.delete('all')
        
        if self.tree_root is None:
            self.create_text(
                self.winfo_width() // 2,
                self.winfo_height() // 2,
                text='Загрузите текст для построения дерева',
                font=('Arial', 14),
                fill='gray'
            )
            return
        
        # Очищаем позиции и вычисляем новые
        self.node_positions = {}
        
        # Вычисляем позиции с новым алгоритмом
        next_leaf_x = [0]  # Используем список для передачи по ссылке
        min_x, max_x = self.calculate_positions(self.tree_root, 0, 50, next_leaf_x)
        
        # Вычисляем смещение для центрирования дерева
        tree_width = max_x - min_x
        canvas_width = self.winfo_width()
        
        # Центрируем дерево
        center_offset = (canvas_width / 2) - (min_x + tree_width / 2)
        
        # Применяем смещение ко всем узлам
        for node_id, (x, y) in list(self.node_positions.items()):
            self.node_positions[node_id] = (x + center_offset, y)
        
        # Рисуем дерево
        self._draw_node(self.tree_root)
    
    def _draw_node(self, node, parent_pos=None):
        """Рекурсивная отрисовка узла и его детей"""
        if node is None:
            return
        
        node_id = id(node)
        if node_id not in self.node_positions:
            return
        
        x, y = self.node_positions[node_id]
        
        # Применяем трансформации
        x = x * self.scale_factor + self.offset_x
        y = y * self.scale_factor + self.offset_y
        radius = self.node_radius * self.scale_factor
        
        # Рисуем линии к детям
        if node.left:
            left_id = id(node.left)
            if left_id in self.node_positions:
                left_x, left_y = self.node_positions[left_id]
                left_x = left_x * self.scale_factor + self.offset_x
                left_y = left_y * self.scale_factor + self.offset_y
                
                self.create_line(
                    x, y + radius,
                    left_x, left_y - radius,
                    width=2 * self.scale_factor,
                    fill='#2c3e50',
                    tags='edge'
                )
                # Подпись "0"
                mid_x = (x + left_x) / 2
                mid_y = (y + left_y) / 2
                self.create_text(
                    mid_x - 10 * self.scale_factor,
                    mid_y,
                    text='0',
                    font=('Arial', int(12 * self.scale_factor), 'bold'),
                    fill='#e74c3c'
                )
        
        if node.right:
            right_id = id(node.right)
            if right_id in self.node_positions:
                right_x, right_y = self.node_positions[right_id]
                right_x = right_x * self.scale_factor + self.offset_x
                right_y = right_y * self.scale_factor + self.offset_y
                
                self.create_line(
                    x, y + radius,
                    right_x, right_y - radius,
                    width=2 * self.scale_factor,
                    fill='#2c3e50',
                    tags='edge'
                )
                # Подпись "1"
                mid_x = (x + right_x) / 2
                mid_y = (y + right_y) / 2
                self.create_text(
                    mid_x + 10 * self.scale_factor,
                    mid_y,
                    text='1',
                    font=('Arial', int(12 * self.scale_factor), 'bold'),
                    fill='#27ae60'
                )
        
        # Определяем цвет узла
        if node.char is not None:
            # Листовой узел
            color = '#3498db'
            text_color = 'white'
        else:
            # Внутренний узел
            color = '#95a5a6'
            text_color = 'white'
        
        # Рисуем круг узла
        self.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=color,
            outline='#2c3e50',
            width=2,
            tags='node'
        )
        
        # Текст в узле
        if node.char is not None:
            # Для листа показываем символ
            display_char = repr(node.char)[1:-1] if node.char != ' ' else '␣'
            if len(display_char) > 3:
                display_char = display_char[:3]
            
            self.create_text(
                x, y - 5 * self.scale_factor,
                text=display_char,
                font=('Arial', int(12 * self.scale_factor), 'bold'),
                fill=text_color,
                tags='text'
            )
            self.create_text(
                x, y + 8 * self.scale_factor,
                text=str(node.freq),
                font=('Arial', int(9 * self.scale_factor)),
                fill=text_color,
                tags='text'
            )
        else:
            # Для внутреннего узла показываем частоту
            self.create_text(
                x, y,
                text=str(node.freq),
                font=('Arial', int(11 * self.scale_factor), 'bold'),
                fill=text_color,
                tags='text'
            )
        
        # Рекурсивно рисуем детей
        self._draw_node(node.left, (x, y))
        self._draw_node(node.right, (x, y))


class HuffmanGUI:
    """Главное окно приложения"""
    
    def __init__(self, root):
        self.root = root
        self.root.title('Кодирование Хаффмана - Визуализация')
        self.root.geometry('1400x800')
        
        self.coder = HuffmanCoder()
        self.current_text = ''
        
        self.setup_ui()
        
    def setup_ui(self):
        """Создание интерфейса"""
        # Главный контейнер
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Левая панель (дерево)
        left_frame = ttk.Frame(main_container)
        main_container.add(left_frame, weight=3)
        
        # Заголовок дерева
        tree_header = ttk.Frame(left_frame)
        tree_header.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(
            tree_header,
            text='🌳 Дерево Хаффмана',
            font=('Arial', 14, 'bold')
        ).pack(side=tk.LEFT)
        
        ttk.Label(
            tree_header,
            text='(Колесо мыши - масштаб, ЛКМ - перемещение)',
            font=('Arial', 9),
            foreground='gray'
        ).pack(side=tk.LEFT, padx=10)
        
        # Canvas для дерева
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.tree_canvas = TreeVisualizer(
            tree_frame,
            highlightthickness=1,
            highlightbackground='#bdc3c7'
        )
        self.tree_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Правая панель (таблица и управление)
        right_frame = ttk.Frame(main_container)
        main_container.add(right_frame, weight=1)
        
        # Панель управления
        control_frame = ttk.LabelFrame(right_frame, text='Управление', padding=10)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Кнопка загрузки текста
        ttk.Button(
            control_frame,
            text='📄 Загрузить текст',
            command=self.load_text
        ).pack(fill=tk.X, pady=2)
        
        # Кнопка ввода текста
        ttk.Button(
            control_frame,
            text='✏️ Ввести текст',
            command=self.enter_text
        ).pack(fill=tk.X, pady=2)
        
        # Разделитель
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Кнопки сжатия/распаковки
        ttk.Button(
            control_frame,
            text='📦 Сжать файл',
            command=self.compress
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            control_frame,
            text='📂 Распаковать файл',
            command=self.decompress
        ).pack(fill=tk.X, pady=2)
        
        # Разделитель
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Кнопка сброса
        ttk.Button(
            control_frame,
            text='🔄 Сбросить масштаб',
            command=self.reset_view
        ).pack(fill=tk.X, pady=2)
        
        # Статистика
        stats_frame = ttk.LabelFrame(right_frame, text='Статистика', padding=10)
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.stats_text = tk.Text(
            stats_frame,
            height=6,
            font=('Courier', 9),
            wrap=tk.WORD
        )
        self.stats_text.pack(fill=tk.X)
        
        # Таблица кодов
        table_frame = ttk.LabelFrame(right_frame, text='📊 Таблица кодов', padding=5)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Создаем таблицу
        columns = ('char', 'code', 'freq')
        self.code_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            height=15
        )
        
        self.code_table.heading('char', text='Символ')
        self.code_table.heading('code', text='Код')
        self.code_table.heading('freq', text='Частота')
        
        self.code_table.column('char', width=60, anchor=tk.CENTER)
        self.code_table.column('code', width=100, anchor=tk.CENTER)
        self.code_table.column('freq', width=60, anchor=tk.CENTER)
        
        # Полоса прокрутки для таблицы
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.code_table.yview)
        self.code_table.configure(yscrollcommand=scrollbar.set)
        
        self.code_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def load_text(self):
        """Загрузка текста из файла"""
        filename = filedialog.askopenfilename(
            title='Выберите текстовый файл',
            filetypes=[('Text files', '*.txt'), ('All files', '*.*')]
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.current_text = f.read()
            
            if not self.current_text:
                messagebox.showwarning('Предупреждение', 'Файл пустой!')
                return
            
            self.build_tree()
            
        except Exception as e:
            messagebox.showerror('Ошибка', f'Не удалось загрузить файл:\n{e}')
    
    def enter_text(self):
        """Ручной ввод текста"""
        dialog = tk.Toplevel(self.root)
        dialog.title('Ввод текста')
        dialog.geometry('600x400')
        
        ttk.Label(
            dialog,
            text='Введите текст для кодирования:',
            font=('Arial', 11)
        ).pack(padx=10, pady=10)
        
        text_widget = scrolledtext.ScrolledText(
            dialog,
            font=('Courier', 10),
            wrap=tk.WORD
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        def on_ok():
            self.current_text = text_widget.get('1.0', tk.END).strip()
            if self.current_text:
                dialog.destroy()
                self.build_tree()
            else:
                messagebox.showwarning('Предупреждение', 'Введите текст!')
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text='OK', command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text='Отмена', command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def build_tree(self):
        """Построение дерева Хаффмана"""
        if not self.current_text:
            return
        
        try:
            # Строим дерево
            freq = self.coder.build_codes(self.current_text)
            
            # Обновляем визуализацию
            self.tree_canvas.set_tree(self.coder.tree)
            
            # Обновляем таблицу
            self.update_table()
            
            # Обновляем статистику
            self.update_statistics(freq)
            
        except Exception as e:
            messagebox.showerror('Ошибка', f'Не удалось построить дерево:\n{e}')
    
    def update_table(self):
        """Обновление таблицы кодов"""
        # Очищаем таблицу
        for item in self.code_table.get_children():
            self.code_table.delete(item)
        
        # Заполняем таблицу
        if not self.coder.codes:
            return
        
        # Сортируем по длине кода, затем по символу
        sorted_items = sorted(
            self.coder.codes.items(),
            key=lambda x: (len(x[1]), x[0])
        )
        
        for char, code in sorted_items:
            # Форматируем символ для отображения
            if char == ' ':
                display_char = '␣ (пробел)'
            elif char == '\n':
                display_char = '↵ (новая строка)'
            elif char == '\t':
                display_char = '⇥ (таб)'
            else:
                display_char = repr(char)[1:-1]
            
            # Получаем частоту
            freq = sum(1 for c in self.current_text if c == char)
            
            self.code_table.insert('', tk.END, values=(display_char, code, freq))
    
    def update_statistics(self, freq):
        """Обновление статистики"""
        self.stats_text.delete('1.0', tk.END)
        
        total_chars = len(self.current_text)
        unique_chars = len(freq)
        
        # Вычисляем размеры
        original_bits = total_chars * 8
        
        encoded_bits = sum(len(self.coder.codes[char]) for char in self.current_text)
        
        compression_ratio = (1 - encoded_bits / original_bits) * 100 if original_bits > 0 else 0
        
        # Средняя длина кода
        avg_code_length = encoded_bits / total_chars if total_chars > 0 else 0
        
        stats = f"""Символов: {total_chars}
Уникальных: {unique_chars}
Исходный размер: {original_bits} бит
Сжатый размер: {encoded_bits} бит
Сжатие: {compression_ratio:.1f}%
Средняя длина кода: {avg_code_length:.2f} бит"""
        
        self.stats_text.insert('1.0', stats)
    
    def compress(self):
        """Сжатие файла"""
        input_file = filedialog.askopenfilename(
            title='Выберите файл для сжатия',
            filetypes=[('Text files', '*.txt'), ('All files', '*.*')]
        )
        
        if not input_file:
            return
        
        output_file = filedialog.asksaveasfilename(
            title='Сохранить как',
            defaultextension='.bin',
            filetypes=[('Binary files', '*.bin'), ('All files', '*.*')]
        )
        
        if not output_file:
            return
        
        try:
            compress_file(input_file, output_file)
            messagebox.showinfo('Успех', 'Файл успешно сжат!')
        except Exception as e:
            messagebox.showerror('Ошибка', f'Не удалось сжать файл:\n{e}')
    
    def decompress(self):
        """Распаковка файла"""
        input_file = filedialog.askopenfilename(
            title='Выберите файл для распаковки',
            filetypes=[('Binary files', '*.bin'), ('All files', '*.*')]
        )
        
        if not input_file:
            return
        
        output_file = filedialog.asksaveasfilename(
            title='Сохранить как',
            defaultextension='.txt',
            filetypes=[('Text files', '*.txt'), ('All files', '*.*')]
        )
        
        if not output_file:
            return
        
        try:
            decompress_file(input_file, output_file)
            messagebox.showinfo('Успех', 'Файл успешно распакован!')
        except Exception as e:
            messagebox.showerror('Ошибка', f'Не удалось распаковать файл:\n{e}')
    
    def reset_view(self):
        """Сброс масштаба и позиции"""
        self.tree_canvas.scale_factor = 1.0
        self.tree_canvas.offset_x = 0
        self.tree_canvas.offset_y = 0
        self.tree_canvas.draw_tree()


def main():
    root = tk.Tk()
    app = HuffmanGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()