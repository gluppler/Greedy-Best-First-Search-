class VirtualWorld:
    def __init__(self, grid, traps, rewards, entry):
        # Initialize the virtual world
        self.grid = grid # Data representation of the world
        self.traps = traps # Dictionary of traps and their effects
        self.rewards = rewards # Dictionary of rewards and their effects
        self.entry = entry # Entry point
        self.cols = len(grid)
        self.rows = len(grid[0])
        self.treasure_positions = self.get_positions('Treasure') # List of treasure positions
        self.visited = set() # Track visited nodes
        self.collected_treasures = 0 # Track collected treasures
        self.logged_positions = [] # Log of visited positions
        self.energy_multiplier = 1
        self.steps_multiplier = 1
        self.last_direction = (0, 0) # Track the last direction moved
        self.treasures_removed = False # Track if treasures have been removed
        self.path = [entry] # Track the path taken
        self.visited_log = []  # Track visited nodes at each step

    # Get all positions of a specific item type in the grid
    def get_positions(self, item_type):
        return [(c, r) for c in range(self.cols) for r in range(self.rows) if self.grid[c][r] == item_type]

    # Check if a position is within the grid bounds
    def in_bounds(self, c, r):
        return 0 <= c < self.cols and 0 <= r < self.rows

    # Apply effects based on the cell type at the given position
    def apply_effects(self, position):
        cell = self.grid[position[0]][position[1]]
        if cell in self.traps:
            return self.handle_trap(cell, position) # Handle trap effects
        if cell in self.rewards:
            return self.handle_reward(cell, position) # Handle reward effects
        return None # if cell is empty or obstacle

    def handle_trap(self, cell, position):
        if cell == 'Trap1':
            self.energy_multiplier *= 2 # Double energy cost
            self.logged_positions.append((position, f"Triggered Trap1: Increased gravity (Energy cost doubles). Energy multiplier: {self.energy_multiplier}, Steps multiplier: {self.steps_multiplier}"))
        elif cell == 'Trap2':
            self.steps_multiplier *= 2 # Double step cost
            self.logged_positions.append((position, f"Triggered Trap2: Decreased speed (Step cost doubles). Energy multiplier: {self.energy_multiplier}, Steps multiplier: {self.steps_multiplier}"))
        elif cell == 'Trap3':
            self.move_two_cells(position) # Move back 2 cells
            self.logged_positions.append((position, f"Triggered Trap3: Moved two cells in last direction. Energy multiplier: {self.energy_multiplier}, Steps multiplier: {self.steps_multiplier}"))
        elif cell == 'Trap4':
            # Remove all uncollected treasures
            if not self.treasures_removed:
                self.treasures_removed = True
                self.treasure_positions.clear()
                self.logged_positions.append((position, "Triggered Trap4: All uncollected treasures have been removed."))
                return True
        return None

    def handle_reward(self, cell, position):
        if cell == 'Reward1':
            self.energy_multiplier *= 0.5 # Halve energy cost
            self.logged_positions.append((position, f"Triggered Reward1: Decreased gravity (Energy cost halves). Energy multiplier: {self.energy_multiplier}, Steps multiplier: {self.steps_multiplier}"))
        elif cell == 'Reward2':
            self.steps_multiplier *= 0.5 # Halve step cost
            self.logged_positions.append((position, f"Triggered Reward2: Increased speed (Step cost halves). Energy multiplier: {self.energy_multiplier}, Steps multiplier: {self.steps_multiplier}"))

    # Move back two cells in the path due to a trap effect
    def move_two_cells(self, position):
        if len(self.path) > 2:
            new_position = self.path[-3]  # Move back 2 steps
            self.entry = new_position  # Update the entry point to the new position
            self.path = self.path[:-2]  # Remove the last 2 steps from the path
            print(f"Moved back to {new_position} due to Trap3")
        return position

    # Calculate the heuristic distance to the nearest treasure position
    # Based on Manhattan distance
    def heuristic(self, position):
        if not self.treasure_positions:
            return float('inf')
        return min(abs(position[0] - tr[0]) + abs(position[1] - tr[1]) for tr in self.treasure_positions)

    # Greedy Best-First Search to collect all treasures in the world
    def gbfs(self):
        total_cost = 0
        treasures_to_find = len(self.treasure_positions)
        priority_queue = [(0, self.entry)]
        visited_positions = set()

        # Log starting position
        self.logged_positions.append((self.entry, "Start"))

        # Search until all possible treasures are found or priority queue is empty
        while self.collected_treasures < treasures_to_find and priority_queue:
            priority_queue.sort() # Sort the queue based on heurstic value (cost)
            cost, position = priority_queue.pop(0)

            if position in visited_positions:
                continue

            self.visited.add(position) # Add position with least heuristic value to visited
            visited_positions.add(position)
            self.entry = position # Update the entry point to the new position
            self.last_direction = (position[0] - self.entry[0], position[1] - self.entry[1]) # Update the last direction moved

            # Calculate distance to the nearest treasure
            nearest_treasure_distance = self.heuristic(position)

            # Log the movement
            self.logged_positions.append((position, f"Moved to {self.grid[position[0]][position[1]]}. Closest distance to next treasure: {nearest_treasure_distance}"))
            self.visited_log.append(position)

            # update total cost
            total_cost += cost

            # Apply effects
            effect_triggered = self.apply_effects(position)

            # if treasure is found
            if position in self.treasure_positions:
                self.treasure_positions.remove(position)
                self.collected_treasures += 1
                self.logged_positions.append((position, "Found a treasure."))

                self.path.append(position)

            if self.collected_treasures == treasures_to_find:
                break 

            if effect_triggered:
                break  # End logging when treasures are removed

            self.explore_adjacent(position, visited_positions, priority_queue)

        return total_cost

    # Explore adjacent nodes based on the current position
    def explore_adjacent(self, position, visited_positions, priority_queue):
        # Even-q offset coordinates
        even_dir = [(0, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)] # even columns
        odd_dir = [(0, -1), (1, -1), (1, 0), (0, 1), (-1, 0), (-1, -1)] # odd columns
        obstacles_traps = {'Obstacle', 'Trap1', 'Trap2', 'Trap4'}

        if position[0] % 2 == 0: # Even column
            for dc, dr in even_dir: # Expand adjacent
                new_c, new_r = position[0] + dc, position[1] + dr
                if self.in_bounds(new_c, new_r) and self.grid[new_c][new_r] not in obstacles_traps:
                    adjacent_position = (new_c, new_r)
                    new_cost = self.heuristic(adjacent_position) * self.energy_multiplier * self.steps_multiplier # Calculate cost considering energy and steps multiplier
                    if adjacent_position not in visited_positions:
                        priority_queue.append([new_cost, adjacent_position]) # Add to priority queue if not visited
                        self.logged_positions.append((adjacent_position, "Exploring adjacent node"))
        else:
            for dc, dr in odd_dir: # Odd column
                new_c, new_r = position[0] + dc, position[1] + dr
                if self.in_bounds(new_c, new_r) and self.grid[new_c][new_r] not in obstacles_traps:
                    adjacent_position = (new_c, new_r)
                    new_cost = self.heuristic(adjacent_position) * self.energy_multiplier * self.steps_multiplier
                    if adjacent_position not in visited_positions:
                        priority_queue.append([new_cost, adjacent_position])
                        self.logged_positions.append((adjacent_position, "Exploring adjacent node"))

    # Print all logged positions
    def print_logged_positions(self):
        print("\nLogged Positions:")
        for position, message in self.logged_positions:
            visited_list=[]
            print(f"Position: {position}, Message: {message}")

            for visited_position in self.visited_log:
                visited_list.append(visited_position)
                if position == visited_position:
                    break
            if 'Moved to' in message:
                print(f"Visited nodes at this step: {visited_list}\n")

    # Print the current grid state, replace grid data with legends
    def print_grid(self):
        legend = {
            'Treasure': 'TS',
            'Reward1': 'R1',
            'Reward2': 'R2',
            'Trap1': 'T1',
            'Trap2': 'T2',
            'Trap3': 'T3',
            'Trap4': 'T4',
            'Obstacle': 'XX',
            'Empty': '[]'
        }
        print("\nCurrent Grid State:")
        for c in range(self.cols):
            line = ''
            if c % 2 == 0:
                line += '  '  # Add extra space for even rows
            for r in range(self.rows):
                cell = self.grid[c][r]
                line += legend.get(cell, cell) + ' '
            print(line)

        print("\nLegends:")
        line = ''
        for key, value in legend.items():
            line += (f"{value}: {key}, ")
        print(line)

# Define the initial grid
# grid is stored in (col,row) format
initial_grid = [
    ['Empty', 'Empty', 'Empty', 'Obstacle', 'Empty', 'Empty'],
    ['Empty', 'Trap2', 'Empty', 'Reward1', 'Empty', 'Empty'],
    ['Empty', 'Empty', 'Obstacle', 'Empty', 'Trap2', 'Empty'],
    ['Empty', 'Trap4', 'Empty', 'Obstacle', 'Treasure', 'Empty'],
    ['Reward1', 'Treasure', 'Obstacle', 'Empty', 'Obstacle', 'Empty'],
    ['Empty', 'Empty', 'Empty', 'Trap3', 'Empty', 'Reward2'],
    ['Empty', 'Trap3', 'Empty', 'Obstacle', 'Obstacle', 'Empty'],
    ['Empty', 'Empty', 'Reward2', 'Treasure', 'Obstacle', 'Empty'],
    ['Empty', 'Obstacle', 'Trap1', 'Empty', 'Empty', 'Empty'],
    ['Empty', 'Empty', 'Empty', 'Treasure', 'Empty', 'Empty']
]

# Define the traps and their effects
traps = {
    'Trap1': 'increase_gravity',
    'Trap2': 'decrease_speed',
    'Trap3': 'move_two_cells',
    'Trap4': 'remove_treasures'
}

# Define the rewards and their effects
rewards = {
    'Reward1': 'decrease_gravity',
    'Reward2': 'increase_speed'
}

# Set the entry point
entry = (0, 0)

# Create the virtual world
virtual_world = VirtualWorld(initial_grid, traps, rewards, entry)

# Print the grid
virtual_world.print_grid()

# Perform the search and calculate the total cost
total_cost = virtual_world.gbfs()

# Print logged positions
virtual_world.print_logged_positions()

# Print the total cost based on treasures collected
if virtual_world.collected_treasures == len(virtual_world.get_positions('Treasure')):
    print(f"All treasures found! Total cost: {total_cost}")
else:
    print(f"Total cost to collect {virtual_world.collected_treasures} treasures: {total_cost}")
