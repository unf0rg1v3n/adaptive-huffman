import sys
from pathlib import Path
import pickle

class BitWriter:
    def __init__(self, file):
        self.file = file
        self.byte = 0
        self.bit_count = 0
    
    def write_bit(self, bit):
        self.byte = (self.byte << 1) | bit
        self.bit_count += 1
        if self.bit_count == 8:
            self.file.write(bytes([self.byte]))
            self.byte = 0
            self.bit_count = 0
    
    def flush(self):
        if self.bit_count > 0:
            self.byte <<= (8 - self.bit_count)
            self.file.write(bytes([self.byte]))

class BitReader:
    def __init__(self, data):
        self.data = data
        self.pos = 0
        self.byte = 0
        self.bit_count = 0
    
    def read_bit(self):
        if self.bit_count == 0:
            if self.pos >= len(self.data):
                return 0
            self.byte = self.data[self.pos]
            self.pos += 1
            self.bit_count = 8
        self.bit_count -= 1
        return (self.byte >> self.bit_count) & 1

class Node:
    def __init__(self, char=None, freq=0):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

class HuffmanCoder:
    def __init__(self):
        self.codes = {}
        self.reverse_codes = {}
        self.tree = None
    
    def build_tree(self, freq_dict):
        """Построение дерева Хаффмана"""
        if not freq_dict:
            return None
        
        # Создаём узлы
        nodes = [Node(char, freq) for char, freq in freq_dict.items()]
        
        if len(nodes) == 1:
            # Особый случай - один уникальный символ
            return nodes[0]
        
        # Строим дерево
        while len(nodes) > 1:
            nodes.sort(key=lambda x: x.freq)
            
            left = nodes.pop(0)
            right = nodes.pop(0)
            
            parent = Node(None, left.freq + right.freq)
            parent.left = left
            parent.right = right
            
            nodes.append(parent)
        
        return nodes[0]
    
    def _generate_codes(self, node, code=''):
        """Генерация кодов"""
        if node:
            if node.char is not None:
                self.codes[node.char] = code if code else '0'
                self.reverse_codes[code if code else '0'] = node.char
            else:
                self._generate_codes(node.left, code + '0')
                self._generate_codes(node.right, code + '1')
    
    def build_codes(self, text):
        """Построение кодов из текста"""
        # Подсчёт частот
        freq = {}
        for char in text:
            freq[char] = freq.get(char, 0) + 1
        
        # Построение дерева
        self.tree = self.build_tree(freq)
        
        # Генерация кодов
        self.codes = {}
        self.reverse_codes = {}
        self._generate_codes(self.tree)
        
        return freq
    
    def encode(self, text):
        """Кодирование текста"""
        result = []
        for char in text:
            result.extend([int(b) for b in self.codes[char]])
        return result
    
    def decode_with_tree(self, reader, length):
        """Декодирование с использованием дерева"""
        result = []
        
        for _ in range(length):
            if self.tree.char is not None:
                # Один уникальный символ
                result.append(self.tree.char)
            else:
                node = self.tree
                while node.char is None:
                    bit = reader.read_bit()
                    node = node.left if bit == 0 else node.right
                result.append(node.char)
        
        return result

def compress_file(input_path, output_path):
    """Сжатие файла"""
    print(f"Чтение {input_path}...", flush=True)
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    if not text:
        print("Файл пустой!")
        return
    
    print(f"Размер: {len(text)} символов", flush=True)
    print("Построение дерева Хаффмана...", flush=True)
    
    # Создаём кодировщик
    coder = HuffmanCoder()
    freq = coder.build_codes(text)
    
    print("Сжатие...", flush=True)
    
    with open(output_path, 'wb') as f:
        # Сохраняем длину текста
        f.write(len(text).to_bytes(4, 'big'))
        
        # Сохраняем таблицу частот
        freq_data = pickle.dumps(freq)
        f.write(len(freq_data).to_bytes(4, 'big'))
        f.write(freq_data)
        
        # Кодируем текст
        writer = BitWriter(f)
        
        for i, char in enumerate(text):
            code = coder.codes[char]
            for bit in code:
                writer.write_bit(int(bit))
            
            if (i + 1) % 100 == 0 or i + 1 == len(text):
                print(f"\r{i + 1}/{len(text)} ({(i+1)*100//len(text)}%)", end='', flush=True)
        
        writer.flush()
    
    print()
    
    original = Path(input_path).stat().st_size
    compressed = Path(output_path).stat().st_size
    ratio = (1 - compressed / original) * 100 if original > 0 else 0
    
    print(f"\n✓ Готово!")
    print(f"  Исходный: {original} байт")
    print(f"  Сжатый: {compressed} байт")
    print(f"  Сжатие: {ratio:.1f}%")

def decompress_file(input_path, output_path):
    """Распаковка файла"""
    print(f"Чтение {input_path}...", flush=True)
    with open(input_path, 'rb') as f:
        # Читаем длину текста
        length = int.from_bytes(f.read(4), 'big')
        
        # Читаем таблицу частот
        freq_len = int.from_bytes(f.read(4), 'big')
        freq_data = f.read(freq_len)
        freq = pickle.loads(freq_data)
        
        # Остальное - закодированные данные
        encoded_data = f.read()
    
    print(f"Распаковка {length} символов...", flush=True)
    print("Восстановление дерева...", flush=True)
    
    # Восстанавливаем дерево
    coder = HuffmanCoder()
    coder.tree = coder.build_tree(freq)
    coder._generate_codes(coder.tree)
    
    # Декодируем
    reader = BitReader(encoded_data)
    result = coder.decode_with_tree(reader, length)
    
    print(f"Запись в {output_path}...", flush=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(''.join(result))
    
    print(f"\n✓ Готово!")

if __name__ == "__main__":
    print("=== Кодирование Хаффмана ===\n", flush=True)
    
    if len(sys.argv) < 4:
        print("Использование:")
        print("  python huffman.py compress input.txt output.bin")
        print("  python huffman.py decompress input.bin output.txt")
        sys.exit(1)
    
    mode, input_file, output_file = sys.argv[1:4]
    
    try:
        if mode == "compress":
            compress_file(input_file, output_file)
        elif mode == "decompress":
            decompress_file(input_file, output_file)
        else:
            print("Режим: compress или decompress")
    except FileNotFoundError:
        print(f"Файл '{input_file}' не найден!")
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()