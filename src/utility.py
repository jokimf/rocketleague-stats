
def conditional_formatting(color: str, value: float, minimum: int, maximum: int) -> str:
    minimum = int(minimum)
    maximum = int(maximum)
    if color is None or (type(value) is not float and type(value) is not int):
        raise ValueError(
            f"Color can not be None and value needs to be int or float: color={color}, value={type(value)}")
    if maximum - minimum == 0:
        return f"{color[:-1]},0)"
    opacity = (value - minimum) / (maximum - minimum)
    rgb_code = f"{color[:-1]},{opacity})"
    return rgb_code

def fade_highlighting(game: int, game_range: int):
    return f"rgba(53, 159, 159,{(game_range - (RLQueries.total_games() - game)) / game_range})"