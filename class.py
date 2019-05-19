class PhoneticAlgorithmIPA:
    
    def __init__(self):
 
        self.default_settings()

    def default_settings(self):
        
        with open('/Users/Stoneberry/Desktop/курсач/4/data/ftable.pickle', 'rb') as f:
            self.feature_table = pickle.load(f)

        with open('/Users/Stoneberry/Desktop/курсач/4/data/index_column.pickle', 'rb') as f:
            self.column_index = pickle.load(f)

        with open('/Users/Stoneberry/Desktop/курсач/4/data/non_ls_dist.pickle', 'rb') as f:
            self.distance_matrix = pickle.load(f)

        with open('/Users/Stoneberry/Desktop/курсач/4/data/rows.pickle', 'rb') as f:
            self.row = pickle.load(f)
    
        # открывать файл с диакритиками
    
        self.feature = {}
   
    
    def stress_number(self, length, word, index, number, current):
        
        '''
        Менять vows и cons при новой таблице
        Сделать разбор на составляющие как в дефолт тейбл
        Обязательно в табилице должно быть syllabic, чтобы различать гласные и согласные
        '''
        
        v = 'The stress is presented incorrectly'
        
        if number < 0: raise ValueError(v)
        if length-1-index < number+1 or word[index+1] != '_': # тут не учитываются случаи типа x͜ⁿ_1 - надо подумать над этим
            raise ValueError(v)

        return [number, number]
    
    
    def affricate(self, current, answer):
        
        global cons
        
        if current.value not in cons or current.previous.value not in cons:
            raise ValueError('Wrong value for an affricate')

        current.value = [current.value, current.previous.value]
        current.vector = [current.vector, current.previous.vector]
        current.previous = current.previous.previous
        answer.pop()
    
    
    def stress_app(self, letter, step, current, answer):
        
        global vows
        
        if letter not in vows:
            raise ValueError('A non vowel element is under stress')
            
        if step[0] == step[1]:
            if step[0] != 1:
                current.value = [current.value]
                current.vector = [current.vector]
        else:
            current.value = current.previous.value + [current.value]
            current.vector = current.previous.vector + [current.vector]
            current.previous = current.previous.previous
            answer.pop()
            
        if step[0] == 1: step = 0
        else: step[0] -= 1

        return step
    

    def letter_parser(self, letter, current, step, answer, index, length):
        
        current.value = letter
        current.vector = letter
        
        if step != 0: current.dia['stress'] = '+'
        
        if current.dia != {}:
            vector = copy.copy(self.feature_table[letter])
            for value in current.dia:
                vector[self.column_index[value]] = current.dia[value]
            current.vector = tuple(vector)
            
        if current.affr:
            self.affricate(current, answer)
            
        if step != 0:
            step = self.stress_app(letter, step, current, answer)

        answer.append(current.vector)
        
        if index != length - 1:
            cur = current
            current.next = Node()
            current = current.next
            current.previous = cur
        
        return current, step


    def transcription_splitter(self, word):
    
        global diacrit
    
        if word == '': return ''
        
        word = word[::-1].lower()
        word = pattern.sub('', word)
        
        length = len(word)
        head = Node()
        answer = []
        current = ''
        step = 0

        for index, letter in enumerate(word):
            
            if index == 0:
                current = head
   
            elif letter.isdigit():
                step = self.stress_number(length, word, index, int(letter), current)
    
            elif letter in diacrit:
        
                if index == length - 1:
                    raise ValueError('{} doest not belong to any sound'.format(letter))
            
                if letter in ('͡', '͜'): current.affr = True
                
                elif letter == '_':  continue
            
                else: 
                    value = diacrit[letter]
                    current.dia[value[0]] = value[1]
                    
            elif letter in self.row:
                current, step = self.letter_parser(letter, current, step, answer, index, length)

            else: raise ValueError('Wrong value: {}'.format(letter))
    
        return answer[::-1]
    
     
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
    
    
    def comparison(self, a, b):
    
        if type(a) == str:
        
            if type(b) == str:  # a vs a
                dist = self.distance_matrix[a][rows[b]]
            else: # a vs stress
                dist = self.sound_dist(self.feature_table[a], b)
    
        if type(a) != str:
            if type(b) == str: # stress vs a
                dist = self.sound_dist(a, self.feature_table[b])
            else: # stress vs stress
                dist = self.sound_dist(a, b)
        return dist
    
    
    def dift_affr(self, a, b):
        '''
        [a] vs [a, i]
        [a] vs [stress, i]
        [a] vs [stress, stress]
        
        [a, i] vs [a, i]
    
        stress vs [stress, stress]
        stress vs [stress, None]
        stress vs [None, None]
        '''
    
        res = set()

        if len(a) == len(b):
            for index, item in enumerate(a):
                dist = self.comparison(item, b[index])
                res.add(dist)
            
        else:
            for item in a:
                for itm in b:
                    dist = self.comparison(item, itm)
                    res.add(dist)
        
        return min(res) + (len(res) - 1)
    
    
    def phone_dist(self, a, b):
    
        if type(a) == str and type(b) == str:         # a vs b
            dist = self.distance_matrix[a][rows[b]]
        
        elif type(a) == str: # a 
            if type(b) is not list:                   # a vs stress
                dist = self.sound_dist(self.feature_table[a], b)
            else:                                     # a vs [a, i]
                dist = self.dift_affr([a], b)
        
        elif type(b) == str: 
            if type(a) is not list:                   # stress vs a
                dist = self.sound_dist(a, self.feature_table[b])
            else:
                dist = self.dift_affr(a, [b])              # [a, i] vs a
    
        elif type(a) == list:
            if type(b) == list:                       # [] vs []
                dist = self.dift_affr(a, b) 
            else:                                     # [] vs stress   
                dist = self.dift_affr(a, [b])
    
        elif type(b) == list:                         # stress vs []
            dist = self.dift_affr(b, [a])
            
        else:                                         # stress vs stress
            dist = self.sound_dist(a, b)
        
        return dist
    
    
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
    
    
    def check_data(self, data):
    
        dists = []
        
        for line in data:
    
            if len(line) != 2:
                raise ValueError('There have to be 2 columns in a line. Check your delimiter.')
            
            if line[0] == line[1]: dist = 0
            elif line[0] == '' and line[1] == '':  dist = 0
            else:
                a = self.transcription_splitter(line[0])
                b = self.transcription_splitter(line[1])
                
                if a == '': dist = len(b)
                if b == '': dist = len(a)
                else:  dist = self.lev_distance(a, b)

            dists.append(dist)
            print(line, dist)

        return dists
    
    
    def dist_matrix(self, data):
        
        leng = len(self.row)
        matrix = {i: [0]*leng for i in self.row}
        
        for i in itertools.combinations_with_replacement(self.row, 2):
            
            a = data[i[0]]
            b = data[i[1]]
            
            result = self.sound_dist(a, b)
            result = truncate(result, 5)
                     
            matrix[i[0]][self.row[i[1]]] = result
            matrix[i[1]][self.row[i[0]]] = result
        
        return matrix
    
    
    def ls_dist_matrix(self, data, irrelevant_features):
        
        if irrelevant_features != []:
            
            for i in irrelevant_features:
                if i not in self.column_index:
                    raise ValueError('Incorrect irrelevant features')
            self.features = irrelevant_features
            
        else:
            index = 0
            for line in data:
                for word in line:
                    for ph in pattern2.findall(word):
                        
                        res = {ind for ind, item in enumerate(self.feature_table[ph]) if item == '0'}
                        if index == 0: self.features = res
                        else: self.features &= res
    
                    index += 1
        
        if self.features != {}:
            for i in self.feature_table:
                x = self.feature_table[i]
                for l in self.features: x.pop(l)
                self.feature_table[i] = x
        
            index = 0
            self.column_index = {} 
            for i in self.column_index:
                if i not in self.features:
                    self.column_index[i] = index
                    index += 1
            self.features = {}
        
        self.distance_matrix = self.dist_matrix(self.feature_table)
     
    
    def add_columns(self, d):
        '''
        sonorant: [+ - 0]
        '''
        
        if not isinstance(d, dict):
            raise ValueError('Incorrect data type')
        
        for name in d:
            
            values = d[name]
        
            if not isinstance(name, str):
                raise ValueError('Incorrect column name type')
            
            if not isinstance(values, list):
                raise ValueError('Incorrect column values type')
                
            if values == [] or name == '':
                raise ValueError('Wrong data type')
                
            if name in self.column_index:
                raise ValueError('Column already exists')
        
            if len(values) != len(self.row):
                raise ValueError('All rows have to be filed')
        
            self.column_index[name] = len(self.column_index)
        
            for item in self.row:
                value = values[self.row[item]]
                if value not in ('+', '-', '0'):
                    raise ValueError('Wrong data type')
                self.feature_table[item].append(value)
        
        self.distance_matrix = self.dist_matrix(self.feature_table)
        
        
    def add_rows(self, d):
        
        '''
        a: [+ - 0]
        '''
        
        global reg, vows, pattern2
        
        if not isinstance(d, dict):
            raise ValueError('Incorrect data type')
        
        for name in d:
            
            values = d[name]
        
            if not isinstance(name, str):
                raise ValueError('Incorrect row value type')
            
            if not isinstance(values, list):
                raise ValueError('Incorrect row values type')
            
            if values == [] or name == '':
                raise ValueError('Wrong data type')
        
            if name in self.row:
                raise ValueError('This sound already exists')
            
            if len(values) != len(self.column_index):
                raise ValueError('All columns have to be filed')
                
            if len(name) != 1:
                raise ValueError('Sound should be one item long')
            
            for val in values:
                if val not in ('+', '-', '0'):
                    raise ValueError('Wrong data type')
            
            self.row[name] = len(self.row)
            self.feature_table[name] = values
            reg += '|' + name
            
            if values[4] == '+': vows += name
            elif values[4] == '-': cons.add(name)
       
        self.distance_matrix = self.dist_matrix(self.feature_table)
        pattern2 = re.compile(reg)
        
    
    def add_diacritics(self, d):
        '''
        diacrit = {'ⁿ': ('nasal', '+')
        '''
        
        global diacrit, pattern, dia
        
        if not isinstance(d, dict):
            raise ValueError('Incorrect data type')
        
        for name in d:
            
            values = d[name]
        
            if not isinstance(name, str):
                raise ValueError('Incorrect row value type')
            
            if not isinstance(values, (list, tuple)):
                raise ValueError('Incorrect row values type')
            
            if len(values) != 2 or name == '':
                raise ValueError('Wrong data type')
        
            if name in diacrit:
                raise ValueError('This diacritic already exists')
                
            if len(name) != 1:
                raise ValueError('Diacritic should be one item long')
                
            if values[0] == '' or values[0] not in self.column_index:
                raise ValueError('Diacritic value should be in feature table')
                
            if values[1] not in ('+', '-'):
                raise ValueError('Wrong diacritic value')
                
            if name in dia: dia.remove(name)
            
            diacrit[name] = values
            pattern = re.compile('|'.join(dia))

    
    def change_feature_table(self, d):
        
        '''
        d = {'a' : {'feature': value}}
        d = {'a': [values]}
        d = {'feature': [values]}
        
        УЧЕСТЬ ДОБАВЛЕНИЕ НОВОГО ЗВУКА В РЕГУЛЯРНЫХ ВЫРАЖЕНИЯХ 
        
        '''
        
        global ftable

        for i in d:
            
            if isinstance(d[i], list):  # d = {'feature': [values]}
                
                if i in self.column_index:
                    
                    if len(d[i]) != len(self.row):
                        raise ValueError('All rows have to be filed')
                    
                    feature = self.column_index[i]
                    
                    for l in self.feature_table:
                        value = d[i][self.row[l]]
                        if value not in ('+', '-', '0'):
                            raise ValueError('Incorrect feature value')
                        self.feature_table[l][feature] = value
                    
                elif i in self.row:
                    if len(d[i]) != len(self.column_index):
                        raise ValueError('All columns have to be filed')
                    
                    for value in d[i]:
                        if value not in ('+', '-', '0'):
                            raise ValueError('Incorrect feature value')
                        
                    self.feature_table[i] = d[i]
                
                else: raise ValueError('Incorrect input data')
                    
            
            elif isinstance(d[i], dict) and i in self.row:
                
                for feature in d[i]:
                    
                    if feature not in self.column_index: raise ValueError('Incorrect feature name')
                    if d[i][feature] not in ('+', '-', '0'):
                        raise ValueError('Incorrect feature value')
                    self.feature_table[i][self.column_index[feature]] = d[i][feature]
                    
            else: raise ValueError('Incorrect input data')
    
        self.distance_matrix = self.dist_matrix(self.feature_table) 
    

    def phonetic_distance(self, path, delimiter=';', typ='Non_LS', irrelevant_features=[]):
  
        if not path.endswith('.csv'):
            raise ValueError('Incorrect file type. It should be csv')
            
        if not os.path.isfile(path):
            raise ValueError('Incorrect file path')
            
        if typ not in ('LS', 'Non_LS'):
            raise ValueError('Incorrect type argument')
            
        if not isinstance(irrelevant_features, list):
            raise ValueError('Wrong irrelevant_features data type!')
        
        if delimiter == '':
            raise ValueError('Delimiter should be filled')
        
        with open(path, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=delimiter)
            data = list(reader)

        if typ == 'LS': self.ls_dist_matrix(data, irrelevant_features)
        
        elif typ == 'Non_LS': 
            
            if irrelevant_features != []:
                raise ValueError('If you want to delete irrelevant features, use "LS" type!')
    
        dist = self.check_data(data)
        
        return dist 
                     
    
    def rule_applier(self, line, data):
    
        if len(line) != 3:
            raise ValueError('There should be 3 columns: Sound1, Sound2, Context')
    
        if line[0] == '':
            raise ValueError('The first column should be filled')
    
        if line[2] == '':
            reg = line[0]
            res = line[1] 

        else:
            if '##' in line[2]:
                rule1 = re.sub('##', r'\\b', line[2])
                rule2 = re.sub('##', '', line[2])
            else: 
                rule1 = line[2]
                rule2 = rule1
            
            reg = re.sub('_', line[0], rule1)
            res = re.sub('_', line[1], rule2)
    
        return re.sub(reg, res, data)
    
                     
    def phonetic_transformer(self, data_path, rules_path, delimiter=';'):
    
        """
        Чувствителен к регистру
        """
    
        if not data_path.endswith('.csv') or not rules_path.endswith('.csv'):
            raise ValueError('Incorrect data type. It should be csv')
            
        if not os.path.isfile(data_path) or not os.path.isfile(rules_path):
            raise ValueError('Incorrect file path')
        
        if delimiter == '':
            raise ValueError('Delimiter should be filled')
    
        with open(rules_path, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=delimiter)
            rules = list(reader)
    
        with open(data_path, 'r') as file:
            data = file.read()

        for line in rules:
            data = self.rule_applier(line, data)
    
        data = csv.reader(data.split('\n'), delimiter=delimiter)
    
        return self.check_data(list(data))
    
    
