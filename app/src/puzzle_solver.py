move_tuples = [
    ('Kirlia', '15', 'E3', 'C3'),
    ('Kirlia', '14', 'B5', 'D6'),
    ('Kirlia', '13', 'A5', 'C6'),
    ('Kirlia', '12', 'F4', 'D6'),
    ('Kirlia', '11', 'E6', 'C6'),
]



class MoveData:
   def __init__(self):
       self.data = []

   def add_entry(self, name, moves, from_pos, to_pos):
       entry = {
           'Name': name,
           'Moves': moves,
           'From': self.convert_position(from_pos),
           'To': self.convert_position(to_pos)
       }
       self.data.append(entry)

   def load_from_tuples(self, tuple_list):
       for tup in tuple_list:
           if len(tup) == 4:
               self.add_entry(tup[0], tup[1], tup[2], tup[3])

   def get_result(self, name, moves):
       for entry in self.data:
           if entry['Name'] == name and entry['Moves'] == moves:
               return {'From': entry['From'], 'To': entry['To']}
       return None

   @staticmethod
   def convert_position(pos):
       column = ord(pos[0].upper()) - ord('A') + 1 
       row = int(pos[1])
       return f"{row},{column}"

move_data = MoveData()
move_data.load_from_tuples(move_tuples)

result = move_data.get_result('abc', 15)