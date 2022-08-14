def margins_arg_parse(margin):
    margins = margin.split(",")
    if len(margins) == 1:
        return [int(margins[0])] * 4
    return [int(m) for m in margins]
    

def expand_box(points, margin_top, margin_left, margin_bottom, margin_right):
    """
    Expand either bbox or 4-points minimal box -- Add margin to original box

    Args:
        points (_type_): _description_
        margin_top (_type_): _description_
        margin_left (_type_): _description_
        margin_bottom (_type_): _description_
        margin_right (_type_): _description_

    Returns:
        _type_: _description_
    """
    if isinstance(points[0], list):
        # suppose points is 1, p2, p3, p4
        return [
            [points[0][0] - margin_left, points[0][1] - margin_top],
            [points[1][0] + margin_right, points[1][1] - margin_top],
            [points[2][0] + margin_right, points[2][1] + margin_bottom],
            [points[3][0] - margin_left, points[3][1] + margin_bottom]
        ]
    else:
        bbox = points
        # suppose bbox is x1, y1, x2, y2
        return [
            bbox[0, 0] - margin_left,
            bbox[1] - margin_top,
            bbox[2] + margin_right,
            bbox[2] + margin_bottom
        ]