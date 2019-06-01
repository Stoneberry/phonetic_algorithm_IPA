import json
import re
import copy
import os
import csv


def open_json(file):
    """
    Открывает json файлы
    """
    with open(file, 'r', encoding='utf-8') as f:
        return json.load(f)


class Node(object):
    """
    Класс для автоматического анализа звуков
    """
    def __init__(self, value=''):
        self.previous = None
        self.vector = value
        self.value = value
        self.affr = False
        self.next = None
        self.dift = False
        self.dia = {}


def clean(text):
    """
    Функция удаляет все знаки препинания
    """
    text = text.translate(str.maketrans('', '', dia))
    return text


def truncate(n, decimals=0):
    """
    Функция для сокращения символов после запятой
    """
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier


def type_letter(item, vows, cons):

    """
    Функция, которая определяет тип звука: гласный / согласный
    """

    if isinstance(item, list):
        if isinstance(item[0], str): return type_letter(item[0], vows, cons)
        elif isinstance(item[0], tuple):
            if item[0][4] == '+': return 'vow'
            elif item[0][4] == '-': return 'cons'
    
    elif item in vows: return 'vow'
    elif item in cons: return 'cons'
    
    return 'None'


def mean(a, b):
    """
    Функция для расчета среднего значения
    """
    return (a + b)/ 2


def no(a, b):
    """
    Функция для отсутсвия нормализации
    """
    return 1


json_paths = ['/Users/Stoneberry/Desktop/курсач/4/diacrit.json',
              '/Users/Stoneberry/Desktop/курсач/4/cons.json',
              '/Users/Stoneberry/Desktop/курсач/4/vows.json']

with open('/Users/Stoneberry/Desktop/курсач/4/regs.txt', 'r', encoding='utf-8') as f:
    reg_all_sounds, reg_comb, dia = f.readlines()
    reg_all_sounds, reg_comb, dia = [reg_all_sounds[:-1], reg_comb[:-1], dia[:-1]]


diacrit, cons, vows = [open_json(i) for i in json_paths]
normal_func = {'mean': mean, 'max': max, 'min': min, False: no}
pattern1 = re.compile(reg_comb)
pattern2 = re.compile(reg_all_sounds)



class PhoneticAlgorithmIPA:
    
    def __init__(self):
 
        self.default_settings()


    def default_settings(self):

        self.feature_table = open_json('/Users/Stoneberry/Desktop/курсач/4/ftable.json')
        self.column_index = open_json('/Users/Stoneberry/Desktop/курсач/4/index_column.json')
        self.distance_matrix = open_json('/Users/Stoneberry/Desktop/курсач/4/non_ls_dist.json')
        self.row = open_json('/Users/Stoneberry/Desktop/курсач/4/rows.json')
    
        self.feature = {}


    def combination_splitter(self, word):
        '''
        Готовит строку к анализу, заменяет комбинации символов
        '''
        word = clean(word)
        length = len(word)
        res = re.findall(pattern1, word)

        if res != []:
           word = re.sub(pattern1, '@', word)
        word  = word[::-1] + '#'
   
        return word, res, length


    def dia_cond1(self, current, vows, cons, step, value):

        a = type_letter(current.value, vows, cons) == 'vow'
        b = current.previous is not None

        if a and b:
            c = type_letter(current.previous.value, vows, cons) == 'vow'
            d = not current.previous.dia.get('stress')
            e = not current.previous.dia.get('secondaty stress')
            f = isinstance(current.previous.value, list) and len(current.previous.value) < 3
            j = not isinstance(current.previous.value, list)
            
            if c and d and e:
                if f or j:
                    current.affr = True

        return current


    def dia_applier(self, current, step, vows, cons):
        
        if isinstance(current.value, list): return current.vector

        if current.dia != {}:
        
##            vector = copy.copy(self.feature_table[current.value])

            for value in current.dia:
    
                current.vector[self.column_index[value]] = current.dia[value]

                if step == 0 and value == 'syllabic' and current.dia[value] == '-':
                    current = self.dia_cond1(current, vows, cons, step, value)

        current.vector = tuple(current.vector)
                                
        return current.vector
    

    def add_value(self, current, answer, letter, step, vows, cons):

            
        answer.append(current.vector)
        cur = current
        
        if current.next is None:
            current.next = Node()
            
        current = current.next
        current.previous = cur

        return current


    def post_diacrit(self, index, length, current, value, letter):

        if index == length - 1: raise ValueError

        if current.value == '':
            if letter == '̯': current.dift = True
            current.dia = {**current.dia, **value[1]}
            
        else:
            if current.next is None: current.next = Node()
            if letter == '̯': current.next.dift = True
            current.next.dia = {**current.next.dia , **value[1]}
        
        return current


    def between_diacrit(self, index, length, current, step):

        if 0 < index != length - 1:
                    
            if current.next is None: current.next = Node()
            
            current.next.affr = True
                        
            if isinstance(current.value, str):
                current.vector = self.dia_applier(current, step, vows, cons)
                current.vector = [current.vector]
                current.value = [current.value]
                current.dift = [current.dift]

        else: raise ValueError

        return current


    def diacritics(self, letter, index, length, current, step):

        value = diacrit[letter] # 'ⁿ': ['post', {'nasal': '+'}]

        if value[0] == 'post':
            current = self.post_diacrit(index, length, current, value, letter)

        elif value[0] == 'pre':
            if current.value == '': raise ValueError
            current.dia = {**current.dia, **value[1]}

        elif value[0] == 'between':
            current = self.between_diacrit(index, length, current, step)
        return current


    def stress_number(self, length, word, index, number, current):
     
        v = 'The stress is presented incorrectly'
        
        if number == 0: raise ValueError(v)
            
        if length-1-index < number+1 or word[index+1] not in ('_', '='):
            raise ValueError(v)
            
        if word[index+1] == '_': typ = 'main'
        elif word[index+1] == '=': typ = 'side'

        return [number, number, typ]


    def stress_app(self, letter, step, current, answer, vows, cons):

        if type_letter(current.value, vows, cons) != 'vow':
            raise ValueError('A non vowel element is under stress')
            
        if step[0] == step[1] and step[0] != 1:
            current.value = [current.value]
            current.vector = [current.vector]
            current.dift = [current.dift]
    
        elif step[0] != step[1]:
            current.value = current.previous.value + [current.value]
            current.vector = current.previous.vector + [current.vector]
            current.dift = current.previous.dift + [current.dift]
            current.previous = current.previous.previous
            answer.pop()
            
        if step[0] == 1: step = 0
        else: step[0] -= 1

        return step


    def affricate(self, current, answer, vows, cons):
  
        current.vector = [current.vector]
        current.value = [current.value]
        current.dift = [current.dift]
        
        if not isinstance(current.previous.value, list):
            current.previous.value = [current.previous.value]
            current.previous.vector = [current.previous.vector]
            current.previous.dift = [current.previous.dift]
            
        current.vector += current.previous.vector
        current.value += current.previous.value
        current.dift += current.previous.dift
        
        if len({type_letter(i, vows, cons) for i in current.value}) != 1:
            raise ValueError('All values should be have the same type')
            
        current.previous = current.previous.previous
        answer.pop()
        return current


    def digit_rule(self, letter, step, current, answer, vows, cons):

        if step != 0:
            if step[0] != 1: raise ValueError('The stress is presented incorrectly')
            
        current, step = self.letter_parser(step, current, '', answer, vows, cons)

        return current, step



    def dia_cond2(self, current, vows, cons):

        if not current.dia.get('syllabic') and current.previous is not None:

            a = type_letter(current.previous.value, vows, cons) == 'vow'
            a0 = current.previous.dia.get('syllabic') == '-'
            b = not current.previous.dia.get('stress')
            b1 = not current.previous.dia.get('secondaty stress')
            c = isinstance(current.previous.value, list) and  False not in current.previous.dift
            d = not isinstance(current.previous.value, list)

            if a and a0 and b and b1:
                if c or d:
                    current.affr = True
        return current
 
    

    def letter_parser(self, step, current, letter, answer, vows, cons, dig=False):

        if step != 0: 
            if step[-1] == 'main': current.dia['stress'] = '+'
            else: current.dia['second stress'] = '+'

        if current.value != '':
            current.vector = self.dia_applier(current, step, vows, cons)

            if step == 0 and type_letter(current.value, vows, cons) == 'vow':
                current = self.dia_cond2(current, vows, cons)

            if step != 0:
                step = self.stress_app(letter, step, current, answer, vows, cons)

            if current.affr:
                current = self.affricate(current, answer, vows, cons)
            
            current = self.add_value(current, answer, letter, step, vows, cons)

        if letter not in ('#', ''): 
            current.value = letter
            current.vector = copy.copy(self.feature_table[letter])
        
        return current, step


    def transcription_splitter(self, word, diacrit, vows, cons):

        if word == '': return ''

        word, replacements, length = self.combination_splitter(word)
        
        answer = []
        current = Node()
        step, index_replace = 0, 0

        for index, letter in enumerate(word):

            if letter == '@':
                letter = replacements[index_replace]
                index_replace += 1

            if letter in ('_', '='): continue

            if letter.isdigit():
                if current.value != '':
                    current, step = self.digit_rule(letter, step, current, answer, vows, cons)
                step = self.stress_number(length, word, index, int(letter), current)

            elif letter in diacrit:
                current = self.diacritics(letter, index, length, current, step)

            elif letter in self.row or letter == '#':
                current, step = self.letter_parser(step, current, letter, answer, vows, cons)
            
            else: raise ValueError('Wrong value: {}'.format(letter))

        return answer[::-1]


## --------------------------------------------------------

    def sound_dist(self, a, b):

        similar, common, uncommon = 0, 0, 0
        
        for index, item in enumerate(a): 
    
            if item == b[index] and item != '0':
                common += 1
                similar += 1
    
            elif item != b[index]:
                if item == '0' or b[index] == '0': uncommon += 1
                else: common += 1
            
        dist = 1 - (similar / (common + (uncommon * 2)))
        return dist


    def different_length(self, a, len_a, b, len_b):

        res = []

        if len_a < len_b:
            a, b = b, a
            len_a, len_b = len_b, len_a

        for i in a:
            r = [self.sound_dist(i, l) for l in b]
            res.append(min(r))

        ans = sum(sorted(res)[:min(len_a, len_b)])

    
        return ans + len_a - len_b


    def equal_length(self, a, b):

        res = [self.sound_dist(it, b[ind]) for ind, it in enumerate(a)]

        return sum(res)
    
    
    def dist_affr(self, a, b):

        len_a, len_b = len(a), len(b)

        if len_a != len_b:
            return self.different_length(a, len_a, b, len_b)
    
        return self.equal_length(a, b)
        
    
    def phone_dist(self, a, b):
        
        if isinstance(a, list) and isinstance(b, list):
            return self.dist_affr(a, b)
        
        if isinstance(a, list) and not isinstance(b, list):
            return self.dist_affr(a, [b])
        
        if isinstance(b, list):
            return self.dist_affr([a], b)
        
        return self.sound_dist(a, b)
    
    
    def lev_distance(self, a, b):
    
        # Первыми - строчки 
        # столбики - слово b
   
        dis = [[0]* (len(b)+1) for _ in range(len(a)+1)]
        size = (len(b)+1) * (len(a)+1)
        i, row, col = 0, 0, 0
        
        while i < size:
          
            if row == 0:
                if col != 0:
                    dis[row][col] = dis[row][col-1] + 1

            elif col == 0:
                if row != 0:
                    dis[row][col] = dis[row - 1][col] + 1
            
            elif row > 2 and col > 2 and a[row-1] == b[col-2] and a[row-2] == b[col-1]:
                dis[row][col] = dis[row - 3][col - 3] + 1
             
            else:
                dis[row][col] = min([dis[row][col - 1] + 1,  # левый 
                                    dis[row - 1][col - 1] + self.phone_dist(a[row-1], b[col-1]), # диаг               
                                    dis[row - 1][col] + 1]) # верхний

            col += 1
            i += 1  

            if col == len(b) + 1:
                col = 0
                row += 1
        
        return dis[len(a)][len(b)]

## --------------------------------------------------------

    def check_data(self, data):

        global diacrit, vows, cons
    
        dists = []
        
        for line in data:
    
            if len(line) != 2:
                raise ValueError('Wrong row number. Check your delimiter')
            
            if line[0] == line[1]: dist = 0
            else:
                a = self.transcription_splitter(line[0], diacrit, vows, cons)
                b = self.transcription_splitter(line[1], diacrit, vows, cons)
                
                if a == '': dist = len(b)
                if b == '': dist = len(a)
                else: dist = self.lev_distance(a, b)

            dists.append(dist)
            print(line, dist)

        return dists


    def phonetic_distance(self, path, delimiter=';', typ='Non LS', irrelevant_features=[]):
  
        if not path.endswith('.csv'):
            raise ValueError('Incorrect file type. It should be csv')
            
        if not os.path.isfile(path):
            raise ValueError('Incorrect file path')
            
        if typ not in ('LS', 'Non LS'):
            raise ValueError('Incorrect type argument')
            
        if not isinstance(irrelevant_features, list):
            raise ValueError('Wrong irrelevant_features data type')
        
        if delimiter == '':
            raise ValueError('Delimiter should be filled')
        
        with open(path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=delimiter)
            data = list(reader)

        if typ == 'LS': self.ls_dist_matrix(data, irrelevant_features)
        
        elif irrelevant_features != []:
            raise ValueError('If you want to delete irrelevant features, use "LS" type!')
    
        dist = self.check_data(data)
        
        return dist 
