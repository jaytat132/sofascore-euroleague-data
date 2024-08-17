from statsPuller import * 

def aggregate_player_stats(shot_map_json):
    player_stats = {}
    # Iterate through each shot in the shot map data
    for shot in shot_map_json['shotmap']:
        player_name = shot['player']['name']  # Get player's name
        if player_name not in player_stats:
            player_stats[player_name] = {
                'shots': 0,
                'goals': 0,
                'blocks': 0,
                'saves': 0,
                'misses': 0,
                'assists': 0,
                'total_shot_distance': 0.0,
                'average_shot_distance': 0.0
            }
        
        # Update shots count
        player_stats[player_name]['shots'] += 1
        
        # Update specific actions
        shot_type = shot['shotType']
        if shot_type == 'goal':
            player_stats[player_name]['goals'] += 1
        elif shot_type == 'block':
            player_stats[player_name]['blocks'] += 1
        elif shot_type == 'save':
            player_stats[player_name]['saves'] += 1
        elif shot_type == 'miss':
            player_stats[player_name]['misses'] += 1
        
        # Calculate total shot distance for average calculation
        player_stats[player_name]['total_shot_distance'] += shot['playerCoordinates']['x']  # assuming x is the distance

        # Update situation-based stats
        situation = shot['situation']
        if situation == 'assisted':
            player_stats[player_name]['assists'] += 1

    # Calculate average shot distance
    for player, stats in player_stats.items():
        if stats['shots'] > 0:
            stats['average_shot_distance'] = stats['total_shot_distance'] / stats['shots']
        del stats['total_shot_distance']  # Remove this as it's no longer needed after averaging
    return player_stats

def extract_dynamic_player_stats(match):
    player_stats = {}
    player_count = {}

    # Iterate directly over the list of shots in the match object
    for shot in match.shotMap_json:
        player_name = shot['player']['slug']
        # Ensure unique naming for each shot by a player
        if player_name in player_count:
            player_count[player_name] += 1
            unique_name = f"{player_name}_{player_count[player_name]}"
        else:
            player_count[player_name] = 1
            unique_name = f"{player_name}_1"

        # Create a dictionary for each shot including all available fields dynamically
        player_stats[unique_name] = {
            'Country': match.home_team if shot['isHome'] else match.away_team,
            'player_name': player_name
        }

        # Include all other details, flattening structures where necessary
        for key, value in shot.items():
            if key == 'player':
                continue  # Skip the 'player' key since the name is already used
            elif key in ['playerCoordinates', 'goalMouthCoordinates', 'blockCoordinates', 'draw']:
                # For nested dictionaries, flatten them
                for subkey, subvalue in value.items():
                    player_stats[unique_name][f"{key}_{subkey}"] = subvalue
            else:
                # Directly include all other details
                player_stats[unique_name][key] = value

    return player_stats






