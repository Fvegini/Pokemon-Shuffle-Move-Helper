import numpy as np
from itertools import combinations
from src import custom_utils, log_utils

log = log_utils.get_logger()

#######FUCTIONS TO THE CLEAR DISRUPTION TAPPER STRATEGY


def find_taps_to_clear_more_disruptions(final_sequence, shape, num_points):
    matrix = np.array(final_sequence).reshape((6,6))
    converted_matrix = np.zeros_like(matrix, dtype=int)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            converted_matrix[i, j] = convert_matrix_clear_disruption_strategy(matrix[i, j], i)
    positions, sum_values = find_best_combination_for_clear_disruptions(converted_matrix, num_points, shape)
    
    final = np.array(converted_matrix.copy(), dtype=str) # Convert to string type
    for point in positions:
        final[point] = "X"
    
    print_3_matrices_side_by_side(matrix,converted_matrix,final)
    log.debug(f"Score for this Clear Disruptions tap is: {sum_values}")
    results_idx = []
    for position in positions:
        results_idx.append(custom_utils.coordinates_to_index(position[0], position[1], start_at_1=False))
    return results_idx
    

def convert_matrix_clear_disruption_strategy(value, row):
    if value == "Barrier_Stage_Added":
        if row in [0, 1]:
            return 99
        elif row in [2, 3, 4]:
            return 50
        elif row == 5:
            return 4
    elif value.startswith("Barrier"):
        if row in [0, 1]:
            return 90
        elif row in [2, 3]:
            return 20
        elif row == 4:
            return 10
        elif row == 5:
            return 2
    elif value in ["Stage_Added", "Metal", "Fog"]:
        return 5
    elif value in ["Wood"]:
        return 3
    elif value == "Air":
        return 0
    return 1


def generate_shape(matrix, point, shape_type='cross'):
    rows, cols = matrix.shape
    x, y = point
    shape = set()
    
    if shape_type == 'cross':
        if 0 <= x < rows and 0 <= y < cols:
            shape.add((x, y))
            if x > 0: shape.add((x-1, y))
            if x < rows-1: shape.add((x+1, y))
            if y > 0: shape.add((x, y-1))
            if y < cols-1: shape.add((x, y+1))
    elif shape_type == 'square':
        if 0 <= x < rows and 0 <= y < cols:
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if 0 <= x + dx < rows and 0 <= y + dy < cols:
                        shape.add((x + dx, y + dy))
    
    return shape

def calculate_sum(matrix, points, shape="cross"):
    total_sum = 0
    seen = set()
    for point in points:
        cross = generate_shape(matrix, point, shape)
        for pos in cross:
            if pos not in seen:
                total_sum += matrix[pos]
                seen.add(pos)
    return total_sum

def find_best_combination_for_clear_disruptions(matrix, num_points=2, shape="cross"):
    rows, cols = matrix.shape
    all_points = [(i, j) for i in range(rows) for j in range(cols)]
    
    max_sum = 0
    best_combination = None
    
    for points in combinations(all_points, num_points):
        current_sum = calculate_sum(matrix, points, shape)
        if current_sum > max_sum:
            max_sum = current_sum
            best_combination = points
            
    return best_combination, max_sum





####### FUCTIONS TO THE MAKE EXTRA MATCHES STRATEGY
def find_taps_to_make_extra_matches(final_sequence, shape="cross", num_points=2):
    replacement_list, replacement_dict = replace_strings_with_numbers(final_sequence)
    names_matrix = np.array(final_sequence).reshape((6,6))
    matrix = np.array(replacement_list).reshape((6,6))

    best_points = None
    best_score = -1
    
    for num_point in range(num_points):
        new_points, new_best_score = find_best_points(matrix, shape=shape, num_points=num_point+1)
        if new_best_score > best_score:
            best_points = new_points

    marked_matrix_pair_cross = erase_shape(matrix, best_points, shape)
    second = np.array(marked_matrix_pair_cross.copy(), dtype=str) # Convert to string type
    for point in best_points:
        second[point] = "X"
    final_matrix_pair_cross = apply_gravity(marked_matrix_pair_cross)
    final_matrix_pair_cross = replace_empty_spots(final_matrix_pair_cross)

    print_4_matrices_side_by_side(names_matrix, matrix, second, final_matrix_pair_cross)
    log.debug(f"Score for this Extra Matches tap is: {best_score}")
    results_idx = []
    if best_score > 0:
        for position in best_points:
            results_idx.append(custom_utils.coordinates_to_index(position[0], position[1], start_at_1=False))
    return results_idx



# Function to create the erasure based on the selected shape
def erase_shape(matrix, points, shape='cross'):
    new_matrix = matrix.copy()
    for (x, y) in points:
        new_matrix[x, y] = -1
        if x > 0:
            new_matrix[x - 1, y] = -1
        if x < new_matrix.shape[0] - 1:
            new_matrix[x + 1, y] = -1
        if y > 0:
            new_matrix[x, y - 1] = -1
        if y < new_matrix.shape[1] - 1:
            new_matrix[x, y + 1] = -1
        if shape == 'square':
            if x > 0 and y > 0:
                new_matrix[x - 1, y - 1] = -1
            if x > 0 and y < new_matrix.shape[1] - 1:
                new_matrix[x - 1, y + 1] = -1
            if x < new_matrix.shape[0] - 1 and y > 0:
                new_matrix[x + 1, y - 1] = -1
            if x < new_matrix.shape[0] - 1 and y < new_matrix.shape[1] - 1:
                new_matrix[x + 1, y + 1] = -1
    return new_matrix

# Function to apply gravity and fill empty spots with '-'
def apply_gravity(matrix):
    new_matrix = matrix.copy()
    for col in range(new_matrix.shape[1]):
        col_data = new_matrix[:, col]
        non_empty = col_data[col_data != -1]
        empty_count = new_matrix.shape[0] - len(non_empty)
        new_col_data = np.append([-1] * empty_count, non_empty)
        new_matrix[:, col] = new_col_data
    return new_matrix

# Function to replace -1 with '-'
def replace_empty_spots(matrix):
    return np.where(matrix == -1, '-', matrix)

def count_sequences(matrix):
    def check_sequence(sequence):
        if len(sequence) < 3:
            return 0
        else:
            return sum(1 for s in sequence if s not in ['-',0,"0"])

    def count_horizontal():
        count = 0
        for row in matrix:
            current_num = None
            current_count = 0
            sequence = []
            for elem in row:
                if elem == current_num:
                    current_count += 1
                    sequence.append(elem)
                else:
                    count += check_sequence(sequence)
                    current_num = elem
                    current_count = 1
                    sequence = [elem]
            count += check_sequence(sequence)
        return count

    def count_vertical():
        count = 0
        for col in range(len(matrix[0])):
            current_num = None
            current_count = 0
            sequence = []
            for row in range(len(matrix)):
                elem = matrix[row][col]
                if elem == current_num:
                    current_count += 1
                    sequence.append(elem)
                else:
                    count += check_sequence(sequence)
                    current_num = elem
                    current_count = 1
                    sequence = [elem]
            count += check_sequence(sequence)
        return count

    return count_horizontal() + count_vertical()



# Function to find the best points given a shape
def find_best_points(matrix, shape='cross', num_points=1):
    best_score = -1
    best_points = None
    for points in combinations(np.ndindex(matrix.shape), num_points):
        test_matrix = erase_shape(matrix, points, shape)
        final_matrix = apply_gravity(test_matrix)
        score = count_sequences(replace_empty_spots(final_matrix))
        if score > best_score:
            best_score = score
            best_points = points
    return best_points, best_score

def replace_strings_with_numbers(strings):
    replacement_dict = {}
    replacement_list = []
    counter = 1

    for s in strings:
        if s == "Air":
            replacement_list.append(-1)
            if "Air" not in replacement_dict:
                replacement_dict["Air"] = -1
        elif s in ["Wood", "Metal", "Stage_Added", "Fog"]:
            replacement_list.append(0)
            if "Disruption" not in replacement_dict:
                replacement_dict["Disruption"] = 0
        else:
            if s not in replacement_dict:
                replacement_dict[s] = counter
                counter += 1
            replacement_list.append(replacement_dict[s])
    
    return replacement_list, replacement_dict



def print_3_matrices_side_by_side(matrix1, matrix2, matrix3, col_width=5):
    for row1, row2, row3 in zip(matrix1, matrix2, matrix3):
        row_str = ''
        for element in row1:
            element_str = str(element)
            if len(element_str) > col_width:
                element_str = element_str[:col_width]
            row_str += f'{element_str:>{col_width}} '
        row_str += '| '
        for element in row2:
            element_str = str(element)
            if len(element_str) > col_width:
                element_str = element_str[:col_width]
            row_str += f'{element_str:>{col_width}} '
        row_str += '| '
        for element in row3:
            element_str = str(element)
            if len(element_str) > col_width:
                element_str = element_str[:col_width]
            row_str += f'{element_str:>{col_width}} '
        log.debug(row_str)

def print_4_matrices_side_by_side(matrix1, matrix2, matrix3, matrix4, col_width=5):
    for row1, row2, row3, row4 in zip(matrix1, matrix2, matrix3, matrix4):
        row_str = ''
        for element in row1:
            element_str = str(element)
            if len(element_str) > col_width:
                element_str = element_str[:col_width]
            row_str += f'{element_str:>{col_width}} '
        row_str += '| '
        for element in row2:
            element_str = str(element)
            if len(element_str) > col_width:
                element_str = element_str[:col_width]
            row_str += f'{element_str:>{col_width}} '
        row_str += '| '
        for element in row3:
            element_str = str(element)
            if len(element_str) > col_width:
                element_str = element_str[:col_width]
            row_str += f'{element_str:>{col_width}} '
        row_str += '| '
        for element in row4:
            element_str = str(element)
            if len(element_str) > col_width:
                element_str = element_str[:col_width]
            row_str += f'{element_str:>{col_width}} '
        log.debug(row_str)